# File content goes here
import cProfile

def run_profiler(func, *args, **kwargs):
    cProfile.run(func, *args, **kwargs)

if __name__ == '__main__':
    # Example usage
    run_profiler(lambda: some_slow_function(10))
