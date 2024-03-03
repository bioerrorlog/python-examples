import torch


def main() -> None:
    x = torch.tensor([1, 2, 3])
    print(x)
    print(x.dtype)

    X = torch.Tensor([1, 2, 3])
    print(X)
    print(X.dtype)


if __name__ == "__main__":
    main()
