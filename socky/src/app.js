import $ from "jquery";
import client from "./client";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

/**
 * @type {ConstrainDOMString}
 */
let currentCamID = null;
/**
 * @type {HTMLVideoElement}
 */
let video = null;
/**
 * @type {HTMLCanvasElement}
 */
let canvas = null;
/**
 *
 * @type {MediaStream}
 */
let currentCamStream = null;
let chunks = [];
let mediaRecorder = null;

let streaming = false; // Whether or not we're currently streaming
const width = 320; // We will scale the photo width to this
let height = 0; // This will be computed based on the input stream
/**
 * @type {number}
 */
async function getVideoDevices() {
  let mediaDevices = await navigator.mediaDevices.enumerateDevices();
  let videoDevices = mediaDevices.filter(
    (device) => device.kind === "videoinput"
  );
  return videoDevices;
}

/**
 *
 * @param {?ConstrainDOMString} deviceId
 * @returns
 */
async function getVideoStream(deviceId) {
  let constraints = {
    audio: false,
  };
  if (deviceId) {
    constraints.video = { deviceId: deviceId };
  } else {
    constraints.video = true;
  }
  if (currentCamStream) {
    currentCamStream.getTracks().forEach((track) => track.stop());
  }
  let stream = await navigator.mediaDevices.getUserMedia(constraints);
  currentCamStream = stream;
  return stream;
}

/**
 *
 * @param {ConstrainDOMString} deviceId
 */
async function setCurrentCam(deviceId) {
  console.log("setCurrentCam", deviceId);
  let videoDevices = await getVideoDevices();
  if (videoDevices.length === 0) {
    return false;
  }
  // if (videoDevices.some((device) => device.deviceId === deviceId)) {
  //   defaultDeviceId = deviceId;
  // }
  // defaultDeviceId = videoDevices[0].deviceId;
  currentCamID = deviceId;
  // alert(`Default device ${defaultDeviceId}`)
  return true;
}

async function startVideoStream() {
  let stream = null;
  try {
    console.log("currentCamID", currentCamID);
    stream = await getVideoStream(currentCamID);
  } catch (err) {
    console.error(`An error occurred: ${err}`);
    return;
  }
  video.srcObject = stream;
  await video.play();
}

async function stopVideoStream() {
  if (currentCamStream) {
    currentCamStream.getTracks().forEach((track) => track.stop());
  }
  currentCamStream = null;
  video.srcObject = null;
  video.pause();
  clearphoto();
}

async function loadVideoDevices() {
  let videoDevices;
  console.log("loading devices...")
  try {
    videoDevices = await getVideoDevices();
  } catch (err) {
    console.error(`An error occurred: ${err}`);
    return [];
  }
  videoDevices.forEach((device) => {
    $("#cam-list").append(`<option class="cam" value="${device.deviceId}">${device.label}</option>`)
  });
  return videoDevices;
}


async function startRecording() {
  mediaRecorder = new MediaRecorder(currentCamStream);
  mediaRecorder.ondataavailable = function (e) {
    chunks.push(e.data);
  }
  mediaRecorder.onstop = () => {
    let blob = new Blob(chunks, { 'type': 'video/mp4;' });
    client.emit("clip", Date.now(), blob);
    chunks = [];
    let videoURL = window.URL.createObjectURL(blob);
    $("#webcam-recording").attr("src", videoURL);
  }
  mediaRecorder.start();

  setTimeout(() => {
    mediaRecorder.stop();
  }, 1000);
}


function startup() {
  loadVideoDevices().then((videoDevices) => {
    if (videoDevices.length === 0) {
      console.error("No video devices found");
      return;
    }
    setCurrentCam(videoDevices[0].deviceId);
  });
  clearphoto();
}

// Fill the photo with an indication that none has been
// captured.

function clearphoto() {
  const context = canvas.getContext("2d");
  const photo = $("#photo");
  context.fillStyle = "#AAA";
  context.fillRect(0, 0, photo.width(), photo.height());

  const data = canvas.toDataURL("image/png");
  photo.attr("src", data);
}

// Capture a photo by fetching the current contents of the video
// and drawing it into a canvas, then converting that to a PNG
// format data URL. By drawing it on an offscreen canvas and then
// drawing that to the screen, we can change its size and/or apply
// other changes before drawing it.

function takepicture() {
  const context = canvas.getContext("2d");
  if (width && height) {
    canvas.width = width;
    canvas.height = height;
    context.drawImage(video, 0, 0, width, height);

    const data = canvas.toDataURL("image/png");
    $("#photo").attr("src", data);
  } else {
    clearphoto();
  }
}
$(() => {
  video = $("#video").get(0);
  canvas = $("#canvas").get(0);

  $("#cam-list").on("change", function () {
    streaming = false;
    setCurrentCam(this.value).then(startVideoStream);
  });
  $("#snap").on("click", function (ev) {
    takepicture();
    ev.preventDefault();
  });
  $("#clear").on("click", function (ev) {
    clearphoto();
    ev.preventDefault();
  });
  $("#start").on("click", function (ev) {
    startVideoStream();
    ev.preventDefault();
  });
  $("#stop").on("click", function (ev) {
    stopVideoStream();
    ev.preventDefault();
  });

  $("#video").on("canplay", (ev) => {
    console.log("canplay");
    let canvas = $("#canvas");
    if (!streaming) {
      height = video.videoHeight / (video.videoWidth / width);

      if (isNaN(height)) {
        height = width / (4 / 3);
      }
      canvas.attr("width", width);
      canvas.attr("height", height);
      streaming = true;
    }
  });

  $("#start-recording").on("click", function (ev) {
    startRecording();
    ev.preventDefault();
  });

  $("")
  $("#chat-message-submit").on("click", function (ev) {
    let message = $("#chat-message-input").val();
    $("#chat-log").append(`<li class='user'>${message}</li>`);
    if (message)
      client.emit("question", message);
    ev.preventDefault();
  });
  startup();
});