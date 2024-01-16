/**
 * @type {ConstrainDOMString}
 */
let currentMicID = null;

/**
 * @type {MediaStream}
 */
let currentMicStream = null;


async function getAudioDevices() {
  let mediaDevices = await navigator.mediaDevices.enumerateDevices();
  let microphoneDevices = mediaDevices.filter(
    (device) => device.kind === "audioinput"
  );
  return microphoneDevices;
}

async function getAudioStream(deviceId) {
  let constraints = {
    video: false,
  };
  if (deviceId) {
    constraints.audio = { deviceId: deviceId };
  } else {
    constraints.audio = true;
  }
  if (currentMicStream) {
    currentMicStream.getTracks().forEach((track) => track.stop());
  }
  let stream = await navigator.mediaDevices.getUserMedia(constraints);
  currentMicStream = stream;
  return stream;
}

async function loadAudioDevices() {
  let microphoneDevices;
  try {
    microphoneDevices = await getAudioDevices();
  } catch (err) {
    console.error(`An error occurred: ${err}`);
    return [];
  }
  microphoneDevices.forEach((device) => {
    $("#mic-list").append(
      `<option class="mic" value="${device.deviceId}">${device.label}</option>`
    );
  });
  return microphoneDevices;
}

async function setCurrentMic(deviceId) {
  console.log("setCurrentMic", deviceId);
  let microphoneDevices = await getAudioDevices();
  if (microphoneDevices.length === 0) {
    return false;
  }
  currentMicID = deviceId;
  return true;
}

async function startAudioStream() {
  let stream = null;
  try {
    console.log("currentMicID", currentMicID);
    stream = await getAudioStream(currentMicID);
  } catch (err) {
    console.error(`An error occurred: ${err}`);
    return;
  }
}

loadAudioDevices().then((microphoneDevices) => {
  if (microphoneDevices.length === 0) {
    console.error("No microphone devices found");
    return;
  }
  setCurrentMic(microphoneDevices[0].deviceId);
});