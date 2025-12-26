import json
import time
import os
import sys
import traceback


class DevNull:
    def write(self, *_):
        pass

    def flush(self):
        pass


def main():
    try:
        os.chdir("/work")
        with open("/work/input.json") as f:
            state = json.load(f)
        namespace = {}
        with open("/work/bot.py", "r") as f:
            code = f.read()
        stdout = sys.stdout
        sys.stdout = DevNull
        try:
            exec(code, namespace)
            if "make_choice" not in namespace:
                raise RuntimeError("make_choice() not found")
            t = time.time()
            result = namespace["make_choice"](*state)
        finally:
            sys.stdout = stdout
        if time.time() - t > 0.6:
            print(json.dumps({}))
            return
        print(json.dumps({"choice": result}))
    except Exception:
        print(json.dumps({
            "choice": "crash",
            "error": traceback.format_exc(limit=3)
        }))


if __name__ == "__main__":
    main()
