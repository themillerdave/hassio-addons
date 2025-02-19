import json
import requests
import asyncio

class HealthChecker:
    # TODO - There should probably be a limit on the number of retry attempts
    
    # An initial delay is useful since the server won't start returning "200" for some time after starting ffmpeg
    INITIAL_DELAY = 30

    def checkHealth(self):        
        # Make request to HLS endpoint. Typically we get a 404 if things are broken.
        hlsResponse = requests.get(url=f'http://localhost/hls/{self.wrapper.camera["cameraname"]}.m3u8')
        return hlsResponse.status_code == 404

    async def start(self):
        print(f'[HealthChecker {self.wrapper.camera["cameraname"]}] Starting health checker.')
        await asyncio.sleep(self.INITIAL_DELAY)
        while True:
            isErrored = self.checkHealth()
            if isErrored:
                # Error detected. Let's increase the error count.
                print(f'[HealthChecker {self.wrapper.camera["cameraname"]}] Error detected.')
                self.wrapper.state.errorCount += 1
            else:
                # It looks like things are working. Let's reset the error count.
                self.wrapper.state.errorCount = 0
            await asyncio.sleep(self.sleepInterval)

    def stop(self):
        # Cancel the running health check task
        print(f'[HealthChecker {self.wrapper.camera["cameraname"]}] Stopping health checker.')
        self.task.cancel()

    def stateHandler(self, event):
        if event.changedProperty == 'isRunning':
            if event.state.isRunning:
                self.task = asyncio.ensure_future(self.start())
            else:
                self.stop()

    def __init__(self, wrapper, sleepInterval):
        self.wrapper = wrapper
        self.sleepInterval = sleepInterval
        self.running = False
        
        # Bind to state changes
        self.wrapper.state.bind_to(self.stateHandler)

