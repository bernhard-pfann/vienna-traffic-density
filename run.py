import argparse

import params.config as conf
from src.calculate_paths import pathfinder
from src.optimize import optimizer


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, help='Choose workflow to run [sim_paths, optimize]')
    parser.add_argument('--iter', type=int, default=20, help='Number of paths to calculate')
    
    args = parser.parse_args()
    mode = args.mode
    n_iter = args.iter

    if mode == "sim_paths":
        X, y = pathfinder(n_iter)

        X.to_csv(conf.output_paths["X"], sep=",", index=False)
        y.to_csv(conf.output_paths["y"], sep=",", index=False)
        print("Simulated paths written to {}".format(conf.root_output))
    
    elif mode == "optimize":
        coefs = optimizer()
        coefs.to_csv(conf.output_paths["coefs"], sep=",", index=True)
        print("Coefficients optimized.")

    else:
        print("Choose appropriate mode [sim_paths, optimize]")


if __name__ == "__main__":
    main()
