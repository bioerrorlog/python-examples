import torch


x = torch.tensor([1, 2, 3])
print(x)
print(x.dtype)

y = torch.tensor([1, 2, 3], dtype=torch.float32)
print(y)
print(y.dtype)

X = torch.Tensor([1, 2, 3])
print(X)
print(X.dtype)

Empty = torch.Tensor()
print(Empty)
print(Empty.dtype)

empty = torch.tensor(())
print(empty)
print(empty.dtype)

# Error
empty_err = torch.tensor()
print(empty_err)
print(empty_err.dtype)
