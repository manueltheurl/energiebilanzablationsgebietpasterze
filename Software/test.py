import matplotlib.pyplot as plt

# 1.

# def f1(x):
#     return 49 + 0.3*x
#
# def f2(x):
#     return 75 + 0.2*x
#
# x_values = range(0, 500)
#
# plt.figure()
#
# for x in x_values:
#     plt.scatter(x, f1(x), color="blue")
#     plt.scatter(x, f2(x), color="green")
#
# plt.grid()
# plt.show()


# 2.
# def y(x):
#     return 1.5*x + 1
#
#
# x_values = range(-3, 4)
#
# plt.figure()
#
# print(list(x_values))
# print(list([y(x) for x in x_values]))
#
#
# for x in x_values:
#     plt.scatter(x, y(x), color="blue")
#
#
# plt.grid()
# plt.show()

# 3.

k = 0.5



def y(x, k, d):
    return k*x + d


def d(y,x,k):
    return y - x*k

d_ = 2

x_values = list(range(-3, 4))
y_values = [y(x, k, d_) for x in x_values]



k = 0.5  # <- abgelesen
# x und y auch ablesen

for x,y in zip(x_values, y_values):
    print(x, y, d(y, x, k))

x_values = range(-3, 4)

plt.figure()

print(list(x_values))
print(list([y(x) for x in x_values]))


for x in x_values:
    plt.scatter(x, y(x), color="blue")


plt.grid()
plt.show()
