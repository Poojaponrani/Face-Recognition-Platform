const express = require("express");
const axios = require("axios");
const cors = require("cors");

const app = express();
app.use(express.json());
app.use(cors());

app.post("/chat", async (req, res) => {
  try {
    const flaskRes = await axios.post("http://localhost:5000/chat", {
      message: req.body.message
    });

    res.json({ response: flaskRes.data.response });
  } catch (err) {
    console.error("⚠️ Error talking to Flask:", err.message);
    res.status(500).json({ response: "⚠️ Failed to get a response from Flask." });
  }
});

app.listen(4000, () => {
  console.log("💬 Node.js proxy running on http://localhost:4000");
});
