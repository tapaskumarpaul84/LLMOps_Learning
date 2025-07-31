import logging
import os
from datetime import datetime

class CustomLogger:
    def __init__(self,log_dr='logs'):
        self.logs_dir=os.path.join(os.getcwd(),log_dr)
        os.makedirs(self.logs_dir,exist_ok=True)
        self.LOG_FILE=f"{datetime.now().strftime('%m-%d-%Y_%H_%M_%S')}.log"
        LOG_FILE_PATH=os.path.join(self.logs_dir,self.LOG_FILE)

        logging.basicConfig(
            filename=LOG_FILE_PATH,
            format="[ %(asctime)s] %(levelname)s %(name)s (line: %(lineno)d) - %(message)s",
            level=logging.INFO
)
    def get_logger(self,name=__file__):
        return logging.getLogger(os.path.basename(name))
    

if __name__=="__main__":
    logger=CustomLogger()
    logger=logger.get_logger(__file__)
    logger.info("Custom logger initialized")