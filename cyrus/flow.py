from cyrus import Agent #, Enviroment
import os 
import configparser
import threading
import time

class cFlow():

    def getInstance():
        if cFlow.instance == None:
            cFlow.instance = cFlow()
        return cFlow.instance

    def __init__(self, states, start_state):
        self.states = states
        self.start_state = start_state
        global env
        env = Environment.getInstance()
        env.flow.current_state = start_state
        #self.env = Environment()
        config = configparser.ConfigParser()
        config.read(os.path.join(os.getcwd(), "config.ini"))

    def run(self):
        def watch_state(self):
            current_state = self.env.flow.current_state
            while True:
                if self.env.flow.current_state != current_state:
                    env.flow.kill_state = True
                    return
                time.sleep(0.1)
        def run_state(self):
            if self.env.flow.current_state:
                self.env.flow.current_state.run()
            time.sleep(1/60)  # Sleep for a short time to reduce CPU usage
            
        watch_thread = threading.Thread(target=self.watch_state)
        run_thread = threading.Thread(target=self.run_state)

        watch_thread.start()
        run_thread.start()

        watch_thread.join()

        if not watch_thread.is_alive():
            run_thread.join() 

    def run_transition(self, transition):
        pass
    
    def terminate(self):
        pass

    def validate_config_file(self, config_file):
        pass

    def check_step(self):
        pass

    def show():
        pass