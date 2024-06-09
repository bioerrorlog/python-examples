import torch


x = torch.tensor([1, 2, 3])
print("x: ", x)
y = x.add(1)
print("y: ", y)
print("x: ", x)


# in-place
print("\nin-place operation:")

x_ = torch.tensor([1, 2, 3])
print("x_: ", x_)
y_ = x_.add_(1)
print("y_: ", y_)
print("x_: ", x_)
