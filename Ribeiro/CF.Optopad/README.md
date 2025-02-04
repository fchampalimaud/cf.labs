# Summary
This package triggers the optogenetic stimulation in response to fly sips detected in the FlyPad.

# Installation

To run the current package download the most recent zip version from [here](https://github.com/fchampalimaud/cf.labs/releases/), and unzip it to a directory in your computer.

To create local version of Bonsai compatible with the package, simply go to the "bonsai" folder inside the your package folder and run (double-click on) the file "Setup.cmd". This creates a file "Bonsai.exe" which you can use to run your program. 

# Usage

To adjust the code to your computer you need to:
1. Set the right COM port in the properties of the LEDArray node.
2. Set the correct filepaths in the properties of the Logging node.
3. Set the experiment time in the DueTime property of the Timer node.
