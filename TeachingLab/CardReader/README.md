# Summary
Reads badge cards and updates a library database

# Installation

To run the current package download the most recent zip version from [here](https://github.com/fchampalimaud/cf.labs/releases/), and unzip it to a directory in your computer.

To create local version of Bonsai compatible with the package, simply go to the "bonsai" folder inside the your package folder and run (double-click on) the file **setup.cmd**. This creates a file **Bonsai.exe** which you can use to run your package. 

# Usage

Run Bonsai.exe and load the desired **CardReader.bonsai** file.

Click on the **Init** node and set the arduino COM pot in the **PortName** property.

Run the code and double-clik on the **DrawCanvas** node to show the visualization. The visualization uses two images **emtpy.jpg** and **eagle2.jpg**. You can simply modify the contents of the images in the project folder while keeping their names.

The file **CardTable.csv** expects a database with two colums separated by a ',': CardNumber,Name. The file **LibraryDatabase.csv** contains the library entrances. It should start only with the header: ID,Name,Booked; and it gets updated automatically. 


