import matplotlib.pyplot as plt
import math

# Function Implementations
def mcl(a, c, M, X0):
    """
    Perform a linear congruential generator (LCG) calculation.

    The linear congruential generator is a method of generating a sequence of 
    pseudo-randomized numbers calculated with a discontinuous piecewise linear 
    equation. It is defined by the recurrence relation:

        X_{n+1} = (a * X_n + c) % M

    Parameters:
    a (int): The multiplier.
    c (int): The increment.
    M (int): The modulus.
    X0 (int): The seed or start value.

    Returns:
    float: The next value in the sequence.
    """
    return math.fmod((a * X0 + c), M)

def mcl_array(a, c, M, X0, N):
    """
    Generates an array of pseudo-random numbers using the multiplicative congruential method.

    Parameters:
    a (int): The multiplier parameter of the MCL method.
    c (int): The increment parameter of the MCL method.
    M (int): The modulus parameter of the MCL method.
    X0 (int): The seed value for the MCL method.
    N (int): The number of pseudo-random numbers to generate.

    Returns:
    list: A list of N pseudo-random numbers generated by the MCL method.
    """
    x = [0] * N
    x[0] = X0
    for i in range(1, N):
        x[i] = mcl(a, c, M, x[i - 1])
    return x

def standardize_array(x, M):
    """
    Normalizes the elements of a list by dividing each element by a given value.

    Parameters:
    x (list of float): The list of numbers to be normalized.
    M (float): The value by which each element of the list will be divided.

    Returns:
    None: The function modifies the list in place.
    """
    for i in range(len(x)):
        x[i] = x[i] / M

def plot_array(x):
    """
    Plots the values of an array using a scatter plot.

    Parameters:
    x (list or array-like): The array of values to be plotted.

    Returns:
    None
    """
    plt.scatter(range(len(x)), x, s=3)
    plt.xlabel('Index')
    plt.ylabel('Value')
    plt.title('Array Values')
    plt.show(block=True)

def save_array_to_txt(x, filename):
    """
    Saves an array of values to a text file, with each value on a new line.

    Parameters:
    x (iterable): The array or iterable containing the values to be saved.
    filename (str): The name of the file where the values will be saved.

    Returns:
    None
    """
    with open(filename, 'w') as file:
        file.writelines(f"{value}\n" for value in x)
