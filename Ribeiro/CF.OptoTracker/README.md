# Summary
This package performs tracking and optogenetic activation of flies in multiple arenas using the CF.Bonfly package. It is an updated version of the a previous code implemented by Dennis Goldschmidt.

# Installation

To run the current package download the most recent zip version from [here](https://github.com/fchampalimaud/cf.labs/releases/), and unzip it to a directory in your computer.

To create local version of Bonsai compatible with the package, simply go to the "bonsai" folder inside the your package folder and run (double-click on) the file "Setup.cmd". This creates a file "Bonsai.exe" which you can use to run your package. 

# Usage

To run the CF.OptoTracker for the first time:
1. Create a set of arenas with ROIs inside them using the Bonsai script ArenasSetting.bonsai and save it into a file. At the moment all the Arenas are required to have at least one ROI inside it (event if it is set outside of the area where the fly moves). 
2. Open OptoTracker.bonsai and set the arena file in the node LoadArenaSettings.
3. Run the file and double-click on the Gui node to open the graphical user interface.

