import argparse



if __name__ == "__main__":
    num = 0
    duration = 0
    filename = "test.txt"
    is_verbose = False
    f_sensitivity = 0.1
    n_trials = 1
    parser = argparse.ArgumentParser("Custom Error: ")
    parser.add_argument('-n','--n_errors', help='No of errors to introduce')
    parser.add_argument('-d','--duration', help='Duration of error in microseconds')
    parser.add_argument('-f','--file_name', help='Name of saved Text File')
    parser.add_argument('-v','--verbose', help='Bool to decide if you want to print on console')
    parser.add_argument('-s','--sensitivity', help='Force Sensitivity')
    parser.add_argument('-nt','--n_trial', help='Number of Trials')

    args = vars(parser.parse_args())
    if args['n_errors'] is not None:
        num = int(args['n_errors'])
    if args['duration'] is not None:
        duration = float(args['duration'])
    if args['file_name'] is not None:
        filename = args['file_name']
    if args['verbose'] is not None:
        is_verbose = bool(args['verbose'])
    if args['sensitivity'] is not None:
        f_sensitivity = float(args['sensitivity'])
    if args['n_trial'] is not None:
        n_trials = int(args['n_trial'])

    print(f"{num}-{duration}-{filename}-{is_verbose}-{f_sensitivity}-{n_trials}")
