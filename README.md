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

## Portuguese

O objetivo desse projeto é a criação de um aplicativo para a observação do comportamento de animais. O aplicativo foi desenvolvida em Python, utilizando a biblioteca Tkinter para GUI e opencv para tratamento de vídeo.

O aplicativo permite:
- carregar um arquivo csv com uma lista de comportamentos e botões vinculados (ex.:behaviors.csv);
- carregar um vídeo para analisar;
- registrar comportamentos com horario correspondentes;
- mude a posição no vídeo com os botões de seta ou dando um timestamp preciso;
- salvar os resultados da observação em um arquivo csv;

Para iniciar o aplicativo, em primeiro lugar, o Python 3 precisa estar instalado na máquina. Além disso, é necessário instalar as seguintes: tkinter, cv2, PIL.
Os arquivos de vídeo e de comportamentos são carregados nos campos correspondentes. O aplicativo foi testado com vídeos 'avi' com o codec 'H.264'. Embora outros formatos e codecs possam funcionar, é recomendado usá-los. Pois eles certamente são suportados pelo opencv, o que pode causar alguns problemas de outra forma.
