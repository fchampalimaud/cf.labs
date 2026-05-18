# Summary
Experimental platform consisting of a mouse running on a virtual environment and colecting rewards as a function of the distance travelled. 

# Installation

To run the current package download the most recent zip version from [here](https://github.com/fchampalimaud/cf.labs/releases/), and unzip it to a directory in your computer.

To create local version of Bonsai compatible with the package, simply go to the "bonsai" folder inside the your package folder and run (double-click on) the file **setup.cmd**. This creates a file **Bonsai.exe** which you can use to run your package. 

# Usage

Run Bonsai.exe and load the desired **.bonsai** file.

While running your code you can edit add/remove/edit objects in your virtual scene dynamically (i.e while the code is running). You can do this by modifying the **.json** files in the **Protocol** directory, saving the file, and press **R** to update your virtual environment:
- The **VR.ParalaxCorridor** loads the **parallax_settings.json**
- The **VR.RewardDistanceCorridor** loads the **default_settings.json**

Use the mouse wheel to move in the environment.


