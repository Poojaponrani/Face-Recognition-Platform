import React from 'react';
import FaceRecognition from './FaceRecognition';
import ChatBox from './ChatBox';

function App() {
  return (
    <div className="App" style={{ textAlign: 'center', padding: '20px' }}>
      <h1>Face Recognition System</h1>
      <FaceRecognition />
      <hr style={{ margin: '40px 0' }} />
      <ChatBox />
    </div>
  );
}

export default App;
