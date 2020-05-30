import pandas as pd
import numpy as np
from numpy import exp


class SnowToSwe:
    def __init__(self):
        # TODO really bad programming style, has to be adapted when there is time for that
        pass

    def convert(self, data, rho_max=401.2588, rho_null=81.19417, c_ov=0.0005104722, k_ov=0.37856737, k=0.02993175,
                       tau=0.02362476, eta_null=8523356, timestep=24, verbose=False):
        # Hobs = data["hs"].tolist()  # TODO
        Hobs = data

        # TODO several checks if data is nan or negativ or whatever

        if np.isnan(np.sum(Hobs)):
            exit("swe.deltasnow: snow depth data must not be NA")
        if not all(i >= 0 for i in Hobs):
            exit("swe.deltasnow: snow depth data must not be negative")
        if Hobs[0] != 0:
            exit("swe.deltasnow: snow depth observations must start with 0")

        # z = data["date"].tolist()  # all times as list

        # TODO check if z is strictly regular, evenly spaced whatever ..

        snowpack_dd = 0

        H = []  # modeled total height of snow at any day [m]
        SWE = []  # modeled total SWE at any day [kg/m2]
        ly = 1  # layer number [-]
        ts = timestep * 3600  # timestep between observations [s]
        g = 9.81  # gravity [ms-2]

        # preallocate matrix as days X layers
        ly_tot = np.count_nonzero(Hobs)  # maximum number of layers [-]
        day_tot = len(Hobs)  # total days from first to last snowfall [-]

        h = np.zeros((ly_tot, day_tot))  # modeled height of snow in all layers [m]
        swe = np.zeros((ly_tot, day_tot))  # modeled swe in all layers [kg/m2]
        age = np.zeros((ly_tot, day_tot))  # age of modeled layers [days]

        # helper
        m = ' ' * day_tot  # vector of (verbose) messages  TODO not really
        prec = - 10 ^ -10  # precision for arithmetic comparisons [-]

        def paste0(*args):  # completely redundant .. but lets keep it for now
            return args

        def paste(*args):  # completely redundant .. but lets keep it for now
            return args

        def warning(*args):  # completely redundant .. but lets keep it for now
            return args

        def msg(m, t, strg):
            pass

            #   if(verbose){
            #     cat(paste(strg))
            #     if(is.null(m[t])){
            #       m[t] <- strg
            #     } else {
            #       m[t] <- paste(m[t],strg)
            #     }
            #   }
            # }

        def dry_metamorphism(h_d, swe_d, age_d, ly_tot, ly, k, rho_max, ts, prec, g):
            # h.d=h[,t];swe.d=swe[,t];age.d=age[,t]

            # snowpack.dd <- NULL

            # .d  -> today
            # .dd -> tomorrow

            # compute overburden for each layer
            # the overburden for the first layer is the layer itself

            swe_hat_d = []
            for i in range(ly_tot):
                swe_hat_d.append(sum(swe_d[i:ly_tot]))

            # dictionary of lists
            snowpack_d = pd.DataFrame({'h': h_d, "swe": swe_d, "swe_hat": swe_hat_d, "age": age_d})
            H_d = sum(snowpack_d['h'])

            a = snowpack_d.head(ly).apply(compactH, axis=1, args=(h_d, k, rho_max, ts, prec, g, eta_null))
            b = pd.DataFrame(np.zeros((ly_tot - ly, 4)))
            b.columns = ['h', "swe", "age", "rho"]

            # snowpack_dd

            nonlocal snowpack_dd  # TODO BAD
            snowpack_dd = pd.concat([a, b])
            # rownames(snowpack.dd.row) << - paste0("dd.layer", 1: nrow(snowpack.dd))
            return snowpack_dd

        def assignH(sp_dd, h, swe, age, H, SWE, t, day_tot):
            if t < day_tot-1:
                h[:, t + 1] = sp_dd['h']  # probably only t TODO not t +1
                swe[:, t + 1] = sp_dd["swe"]
                age[:, t + 1] = sp_dd["age"]
                H.append(sum(h[:, t + 1]))
                SWE.append(sum(swe[:, t + 1]))

            return {'h': h, "swe": swe, "age": age, 'H': H, "SWE": SWE}

        def drenchH(t, ly, ly_tot, day_tot, Hobs, h, swe, age, H, SWE, rho_max, c_ov, k_ov, k, ts, prec, m):
            Hobs_d = Hobs[t]
            h_d = h[:, t]
            swe_d = swe[:, t]
            age_d = age[:, t]

            msg(m, t, paste("melt "))

            runoff = 0

            # distribute mass top-down
            if t == 143:
                print()

            for i in reversed(range(ly)):
                if sum([element for j, element in enumerate(h_d) if j != i]) + swe_d[i] / rho_max - Hobs_d >= prec:
                    # layers is densified to rho_max
                    h_d[i] = swe_d[i] / rho_max
                else:
                    # layer is densified as far as possible
                    # but doesnt reach rho_max
                    h_d[i] = swe_d[i] / rho_max + abs(
                        sum([element for j, element in enumerate(h_d) if j != i]) + swe_d[i] / rho_max - Hobs_d)
                    break

            # all layers have rho_max
            """
            # TODO for t==228 -5. in this list is false here if not rounded, in r only 6 digits are concerned apparently
            # so as quick "fix" we round it here as well. Max value with rounding: 282.25331288401486, without: 293.52567305443085
            # so it kind of does make a difference
            """

            true_false_list = [round(rho_max - swe_d_val / h_d_val, 6) <= prec for swe_d_val, h_d_val in
                               zip(swe_d[:ly], h_d[:ly])]

            if all(true_false_list):
                msg(m, t, paste("no further compaction "))
                # produce runoff if sum(h_d) - Hobs_d is still > 0
                # if ( sum(h_d) - Hobs_d > prec ){
                msg(m, t, paste("runoff "))
                # decrease swe from all layers?
                # or beginning with lowest?
                # swe_d[1:ly] <- swe_d[1:ly] - (sum(h_d) - Hobs_d) * rho_max
                scale = Hobs_d / sum(h_d)
                runoff = (sum(h_d) - Hobs_d) * rho_max  # excess is converted to runoff [kg/m2]
                h_d = h_d * scale  # all layers are compressed (and have rho_max) [m]
                swe_d = swe_d * scale
            #
            else:
                msg(m, t, paste("compaction "))

            #
            h[:, t] = h_d
            swe[:, t] = swe_d
            age[:, t] = age_d
            H[t] = sum(h[:, t])
            SWE[t] = sum(swe[:, t])
            #
            # no further compaction possible
            # snowpack_tomorrow <- cbind(h = h_d, swe = swe_d, age = age_d, rho = swe_d/h_d)
            # colnames(snowpack_tomorrow) <- c("h","swe","age","rho")
            snowpack_tomorrow = dry_metamorphism(h[:, t], swe[:, t], age[:, t], ly_tot, ly, k, rho_max, ts, prec, g)

            # set values for next day
            rl = assignH(snowpack_tomorrow, h, swe, age, H, SWE, t, day_tot)
            h = rl["h"]
            swe = rl["swe"]
            age = rl["age"]
            H = rl["H"]
            SWE = rl["SWE"]

            return {'h': h, "swe": swe, "age": age, 'H': H, "SWE": SWE}

        def scaleH(t, ly, ly_tot, day_tot, deltaH, Hobs, h, swe, age, H, SWE, rho_max, k, ts, prec, m):
            # re-compact snowpack from yesterdays values with adapted eta
            # .d  -> yesterday
            # .dd -> today
            Hobs_d = Hobs[t - 1]

            Hobs_dd = Hobs[t]
            h_d = h[:, t - 1]
            swe_d = swe[:, t - 1]
            age_d = age[:, t]  # ; deltaH.d = deltaH

            # todays overburden
            swe_hat_d = []
            for i in range(ly_tot):
                swe_hat_d.append(sum(swe_d[i:ly_tot]))

            # analytical solution for layerwise adapted viskosity eta
            # assumption: recompaction ~ linear height change of yesterdays layers (see paper)
            eta_cor = []
            for i in range(ly_tot):
                rho_d = swe_d[i] / h_d[i]
                x = ts * g * swe_hat_d[i] * exp(-k * rho_d)  # yesterday
                P = h_d[i] / Hobs_d  # yesterday
                eta_i = Hobs_dd * x * P / (h_d[i] - Hobs_dd * P)
                eta_cor.append(0 if np.isnan(eta_i) else eta_i)

            # compute H of today with corrected eta
            # so that modeled H = Hobs
            h_dd_cor = np.array(h_d) / (1 + (np.array(swe_hat_d) * g * ts) / np.array(eta_cor) * exp(
                -k * np.array(swe_d) / np.array(h_d)))
            h_dd_cor[np.isnan(h_dd_cor)] = 0  # replace nan with 0
            H_dd_cor = sum(h_dd_cor)
            #
            # and check, if Hd.cor is the same as Hobs.d
            if abs(H_dd_cor - Hobs_dd) > prec:
                warning(
                    paste0("day ", t, ": error in exponential re-compaction: H.dd.cor-Hobs.dd=", H_dd_cor - Hobs_dd))

            # which layers exceed rho.max?
            idx_max = []
            for i, (swe_e_val, h_dd_cor_val) in enumerate(zip(swe_d, h_dd_cor)):
                if swe_e_val / h_dd_cor_val - rho_max > prec:
                    idx_max.append(i)  # TODO +1 each?? cause layers?

            # idx_max = np.where(, swe_d, h_dd_cor)[0]  # [0] cause tuple with list is returned
            if len(idx_max) > 0:
                if len(idx_max) < ly:
                    # collect excess swe in those layers
                    swe_excess = swe_d[idx_max] - h_dd_cor[idx_max] * rho_max  # TODO working?  list of indexes idx_max

                    # set affected layer(s) to rho.max
                    swe_d[idx_max] = swe_d[idx_max] - swe_excess

                    # distribute excess swe to other layers top-down
                    lys = range(1, ly)
                    lys = [element for j, element in enumerate(lys) if j != idx_max]
                    i = lys[len(lys) - 1]
                    swe_excess_all = sum(swe_excess)

                    while swe_excess_all > 0:
                        swe_res = h_dd_cor[i] * rho_max - swe_d[i]  # layer tolerates this swe amount to reach rho.max
                        if swe_res > swe_excess_all:
                            swe_res = swe_excess_all

                        swe_d[i] = swe_d[i] + swe_res
                        swe_excess_all = swe_excess_all - swe_res
                        i = i - 1
                        if i <= 0 and swe_excess_all > 0:
                            msg(m, t, paste(" runoff"))
                            break
                else:
                    # if all layers have density > rho.max
                    # remove swe.excess from all layers (-> runoff)
                    # (this sets density to rho.max)
                    swe_excess = swe_d[idx_max] - h_dd_cor[idx_max] * rho_max
                    swe_d[idx_max] = swe_d[idx_max] - swe_excess
                    msg(m, t, paste(" runoff"))
            #
            # # if(any(na.omit(swe.d/h.dd.cor) - rho.max > prec)){
            # #      stop()
            # # }
            #
            h[:, t] = h_dd_cor
            swe[:, t] = swe_d
            age[:, t] = age_d
            H[t] = sum(h[:, t])
            SWE[t] = sum(swe[:, t])

            # compact actual day
            # if all layers already have maximum density rho_max
            # the snowpack will not be changed by the following step
            # nonlocal or not?????
            snowpack_tomorrow = dry_metamorphism(h[:, t], swe[:, t], age[:, t], ly_tot, ly, k, rho_max, ts, prec, g)

            # set values for next day
            rl = assignH(snowpack_tomorrow, h, swe, age, H, SWE, t, day_tot)
            h = rl["h"]
            swe = rl["swe"]
            age = rl["age"]
            H = rl["H"]
            SWE = rl["SWE"]

            return {'h': h, "swe": swe, "age": age, 'H': H, "SWE": SWE}

        def compactH(x, H_d, k, rho_max, ts, prec, g, eta_null):
            # .d  -> today
            # .dd -> tomorrow
            age_d = 0 if x[0] == 0 else x[3]
            h_dd = x[0] / (1 + (x[2] * g * ts) / eta_null * exp(-k * x[1] / x[0]))
            h_dd = x[1] / rho_max if x[1] / h_dd > rho_max else h_dd
            h_dd = 0 if x[0] == 0 else h_dd
            swe_dd = x[1]
            age_dd = 0 if x[0] == 0 else age_d + 1
            rho_dd = 0 if x[0] == 0 else swe_dd / h_dd
            rho_dd = rho_max if rho_max - rho_dd < prec else rho_dd
            # return [h_dd, swe_dd, age_dd, rho_dd]
            # return x
            df = pd.DataFrame(columns=['h', "swe", "age", "rho"])
            df.loc[0] = [h_dd, swe_dd, age_dd, rho_dd]

            return pd.Series([h_dd, swe_dd, age_dd, rho_dd], index=['h', "swe", "age", "rho"])

        if verbose:
            print("Using parameters:")
            print("rho.max  =", rho_max)
            print("rho.null =", rho_null)
            print("c.ov     =", c_ov)
            print("k.ov     =", k_ov)
            print("k        =", k)
            print("tau      =", tau)
            print("eta.null =", eta_null)

        for t in range(day_tot):
            msg("day", t, ": ")

            # snowdepth = 0, no snow cover
            if Hobs[t] == 0:
                if t > 0:
                    if Hobs[t - 1] == 0:
                        msg(m, t, paste0(""))
                    else:
                        msg(m, t, paste0("runoff"))
                else:
                    msg(m, t, paste0(""))

                try:  # actually brutally bad written, but whatever
                    H[t] = 0  # DIFFERENCE: H is a number, cannot index to it, in R you can
                    SWE[t] = 0
                except IndexError:
                    H.append(0)
                    SWE.append(0)
                h[:, t] = 0  # first column to 0
                swe[:, t] = 0
            # there is snow
            elif Hobs[t] > 0:  # redundant if, cause can snow height be negative?
                # first snow in/during season
                if Hobs[t - 1] == 0:
                    ly = 1
                    msg(m, t, paste("produce layer", ly))
                    age[ly - 1, t] = 1
                    h[ly - 1, t] = Hobs[t]
                    H.append(Hobs[t])  # DIFFERENCE: H is a number, cannot index to it, in R you can
                    swe[ly - 1, t] = rho_null * Hobs[t]
                    SWE.append(swe[ly, t])  # DIFFERENCE: SWE is a number, cannot index to it, in R you can

                    # compact actual day
                    snowpack_tomorrow = dry_metamorphism(h[:, t], swe[:, t], age[:, t], ly_tot, ly, k, rho_max, ts,
                                                         prec, g)

                    # set values for next day TODO GO ON HERE
                    rl = assignH(snowpack_tomorrow, h, swe, age, H, SWE, t, day_tot)  # Todo probably error in here
                    h = rl['h']
                    swe = rl["swe"]
                    age = rl["age"]
                    H = rl['H']
                    SWE = rl["SWE"]
                    # TODO go on 364

                elif Hobs[t - 1] > 0:  # TODO -2?
                    deltaH = Hobs[t] - H[t]
                    # if t + 1 >= 173:
                    #     print(Hobs[t])
                    #     print(H[t])
                    #     print()

                    if deltaH > tau:
                        msg(m, t, paste("create new layer", ly))
                        sigma_null = deltaH * rho_null * g
                        epsilon = c_ov * sigma_null * exp(-k_ov * snowpack_dd["rho"] / (rho_max - snowpack_dd["rho"]))
                        h[:, t] = (1 - epsilon) * h[:, t]
                        # epsilon <- 1 - c.ov * sigma.null * exp(-k.ov * snowpack.dd$rho/(rho.max - snowpack.dd$rho))
                        # h[,t]     <- epsilon * h[,t]
                        swe[:, t] = swe[:, t - 1]
                        age[:ly - 1, t] = age[ly - 1, t - 1] + 1
                        H[t] = sum(h[:, t])
                        SWE[t] = sum(swe[:, t])

                        if t == 142:
                            print(H[t])

                        # RHO[t]    <- SWE[t]/H[t]

                        # only for new layer
                        ly = ly + 1
                        h[ly - 1, t] = Hobs[t] - H[t]
                        swe[ly - 1, t] = rho_null * h[ly - 1, t]
                        age[ly - 1, t] = 1

                        # recompute
                        H[t] = sum(h[:, t])

                        SWE[t] = sum(swe[:, t])

                        # compact actual day
                        snowpack_tomorrow = dry_metamorphism(h[:, t], swe[:, t], age[:, t], ly_tot, ly, k, rho_max, ts,
                                                             prec, g)

                        # set values for next day
                        rl = assignH(snowpack_tomorrow, h, swe, age, H, SWE, t, day_tot)
                        h = rl["h"]
                        swe = rl["swe"]
                        age = rl["age"]
                        H = rl["H"]
                        SWE = rl["SWE"]

                    # no mass gain or loss, but scaling
                    elif deltaH >= -tau and deltaH <= tau:
                        msg(m, t - 1, paste("scaling: "))
                        rl = scaleH(t, ly, ly_tot, day_tot, deltaH, Hobs, h, swe, age, H, SWE, rho_max, k, ts, prec, m)
                        h = rl["h"]
                        swe = rl["swe"]
                        age = rl["age"]
                        H = rl["H"]
                        SWE = rl["SWE"]

                    elif deltaH < -tau:
                        msg(m, t, paste("drenching: "))
                        rl = drenchH(t, ly, ly_tot, day_tot, Hobs, h, swe, age, H, SWE, rho_max, c_ov, k_ov, k, ts,
                                     prec, m)
                        h = rl["h"]
                        swe = rl["swe"]
                        age = rl["age"]
                        H = rl["H"]
                        SWE = rl["SWE"]

                    else:
                        msg(m, t - 1, "??")
        return SWE


if __name__ == "main":
    hsdata = pd.read_csv("hsdata.csv")
    snow_to_swe = SnowToSwe()
    swe = snow_to_swe.convert(hsdata)
    print(max(swe))  # results match
