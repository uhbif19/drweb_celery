import sys

try:
    import drweb_engine.tasks as tasks
except:
    import tasks

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        # Под Windows не работает стандартны prefork-режим 
        tasks.queue.worker_main(["-P", "solo"]+sys.argv)
    else:
        tasks.queue.worker_main()