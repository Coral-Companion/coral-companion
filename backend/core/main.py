# This exists to that code under app/ and code under third-party/ 
# can be run eg. by using 
# functions-framework --target process_coral_upload --debug

# this import prepares sql domain objects
import app.domain

# these 3 lines make sure there is no interactive gui loading for matplotlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# main process
from app.main import process_coral_upload