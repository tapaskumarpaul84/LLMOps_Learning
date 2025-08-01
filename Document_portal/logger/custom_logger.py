import logging
import os
from datetime import datetime
import structlog

class CustomLogger:
    def __init__(self,log_dr='logs'):
        self.logs_dir=os.path.join(os.getcwd(),log_dr)
        os.makedirs(self.logs_dir,exist_ok=True)
        self.log_file=f"{datetime.now().strftime('%m-%d-%Y_%H_%M_%S')}.log"
        self.log_file_path=os.path.join(self.logs_dir,self.log_file)

        

    def get_logger(self,name=__file__):
        logger_name=os.path.basename(name)
        # configure logging for console + file (json format) both
        file_handler=logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(message)s")) # raw json lines

        console_handler=logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        
        logging.basicConfig(
            format="%(message)s",  # structlog will handle json formatting
            level=logging.INFO,
            handlers=[console_handler,file_handler])
        
        # configure structlog for the JSON structure logging

        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt='iso',utc=True,key='timestamp'),
                structlog.processors.add_log_level,
                structlog.processors.EventRenamer(to='event'),
                structlog.processors.JSONRenderer()
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True
        )
        return structlog.get_logger(logger_name)



if __name__=="__main__":
    logger=CustomLogger().get_logger(__file__)
    logger.info("User uploaded a file", user_id=123, filename="report.pdf")
    logger.error("Failed to process PDF", error="File not found", user_id=123)