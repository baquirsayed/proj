function test() {

  window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.lang = 'en-IN';
recognition.interimResults = false;
recognition.maxAlternatives = 1;

const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');

startBtn.addEventListener('click', () => {
  recognition.start();
});

stopBtn.addEventListener('click', () => {
  recognition.stop();
});

recognition.addEventListener('result', (event) => {
    transcript = event.results[0][0].transcript;
  console.log(transcript);

  // Send the transcript text to a Flask route
  fetch('/send_email', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ text: transcript })
  });
});

recognition.addEventListener('end', () => {
  recognition.start();
});

}