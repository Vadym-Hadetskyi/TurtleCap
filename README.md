# TurtleCap

This project has creation of the application for observation of animals' behavior as its goal. The application was developped in Python, using Tkinter library for GUI and opencv to treat video. 

The application allows to:
- load csv with a list of behaviors and linked buttons (ex.:behaviors.csv);
- load a video to analyze;
- register behaviors with corresponding timestamps;
- change the position in the video with with arrow buttons or by giving precise timestamp;
- save the results of the observation in a csv file.

To launch the application, first of all, Python 3 needs to be installed on the machine. Also, besides, standard set of the libraries, it is necessary to install next ones: tkinter, cv2, PIL.
Video and behaviors files are loaded by putting paths to them in the corresponding fields. The application was tested with 'avi' videos with 'H.264' codec. Although other formats and codecs might work, it is recommended to use these, as they are certainly supported by opencv, which may cause some troubles otherwise.
