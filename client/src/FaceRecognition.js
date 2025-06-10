import React, { useRef, useState } from "react";
import Webcam from "react-webcam";
import axios from "axios";

const FaceRecognition = () => {
  const webcamRef = useRef(null);
  const [name, setName] = useState("");
  const [status, setStatus] = useState("");
  const [recognizedNames, setRecognizedNames] = useState([]);

  const captureImage = () => {
    return webcamRef.current.getScreenshot();
  };

  const registerFace = async () => {
    const imageSrc = captureImage();
    if (!name) {
      setStatus("Please enter a name before registering.");
      return;
    }
    try {
      const res = await axios.post("http://localhost:5000/register", {
        name,
        image: imageSrc,
      });
      if (res.data.status === "success") {
        setStatus(` Registered face for ${name}`);
        setName("");
      } else {
        setStatus(" Registration failed: " + res.data.reason);
      }
    } catch (err) {
      setStatus(" Server error during registration.");
    }
  };

  const recognizeFace = async () => {
    const imageSrc = captureImage();
    try {
      const res = await axios.post("http://localhost:5000/recognize", {
        image: imageSrc,
      });
      if (res.data.status === "success") {
        setRecognizedNames(res.data.names);
        setStatus(` Recognized: ${res.data.names.join(", ")}`);
      } else {
        setStatus(" Recognition failed: " + res.data.reason);
      }
    } catch (err) {
      setStatus(" Server error during recognition.");
    }
  };

  return (
    <div style={{ textAlign: "center", padding: 20 }}>
      
      <Webcam
        audio={false}
        ref={webcamRef}
        screenshotFormat="image/jpeg"
        width={400}
        videoConstraints={{ facingMode: "user" }}
      />
      <div style={{ marginTop: 10 }}>
        <input
          type="text"
          placeholder="Enter name to register"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ padding: 5, marginRight: 10 }}
        />
        <button onClick={registerFace} style={{ padding: "5px 10px" }}>
          Register Face
        </button>
      </div>
      <div style={{ marginTop: 10 }}>
        <button onClick={recognizeFace} style={{ padding: "5px 10px" }}>
          Recognize Face
        </button>
      </div>
      <p>{status}</p>
      {recognizedNames.length > 0 && (
      <p>
        Recognized names: <b>{recognizedNames.join(", ")}</b>
        </p>
      )}
    </div>
  );
};

export default FaceRecognition;
