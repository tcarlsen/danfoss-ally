# Danfoss Ally

This is a custom component for Home Assistant to integrate the Danfoss Ally termostats

**OBS! this is under development. use at your own risk!**

## Install

You can install it manually by copying the custom_component folder to your Home Assistant configuration folder.

## Setup

First of all you need to go at get an api key and secret

1. Navigate to https://developer.danfoss.com
2. Create danfoss profile account and login
5. Go to https://developer.danfoss.com/my-apps and click "New App"
6. Lets call it "home-assistant" and describe it as "Smart home solution for Home Assistant"
7. Make sure to enable Danfoss Ally API
8. Click create
9. Copy your key add secret, and add them in your configuration

```yaml
# configuration.yaml
danfoss_ally:
  key: KEY
  secret: SECRET
```
