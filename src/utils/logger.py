import traceback

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ErrorLogger:
    @staticmethod
    def log_error(error: Exception):
        colors = bcolors()
        print(f"{colors.FAIL}[ERROR]{colors.ENDC} - server error: {error}")
        
        print()
        print("******* TRACEBACK *******")
        traceback.print_exc()
        print("******* END TRACEBACK *******")
        print()

        with open("../data/errors.log", "a") as f:
            f.write(f"{error}\n")
            traceback.print_exc(file=f)
            f.write("\n\n")