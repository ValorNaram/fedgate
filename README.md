# FedGate

**FedGate API server written in python3 and using cherrypy as a server framework. FedGate is a highly customizable oAuth gate which allows to hide your content behind an oAuth gate.**

You may run into situations where you just want content to be seen by your community but to hide content from eyedropping people lurcking behind you. This is where FedGate comes in. It comes as fossy and highly customizable as possible and thereof allows as many Use Cases as possible.  If you here because you want to close the doors for eyedropping people, then FedGate could help you.

## Use Case

- Various OpenStreetMap groups on Telegram want just OSMlers in their group but not people having to do with Bitcoin, investment or illegal stuff.
  
  - With FedGate they can now make their groups private and create a list of them which only shows up when someone logs in using their OpenStreetMap account. This way they can hide their groups from eyedrops but at the same time get the members they want --> other OpenStreetMap enthusiasts.

- A Secret wants to be only shown to few who has prooven themselves worthy
  
  - With FedGate the gatekeeper can now share secrets to just a handful of people having a valid oAuth login.

# Thank You

- @hauke96 for explaining me the security/cryptographic and oauth stuff :)
- Thank you Rory for the idea
