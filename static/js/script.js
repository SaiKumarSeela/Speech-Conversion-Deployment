let isRecording = false;
let transcript = "";
let websocket;
let recognition;
let userAnswer = "";
let words = "";
let speakers_transcription = [];
let transcriptionHistory = [];
let stats = {
    duration: 0,
    processingTime: 0,
    totalWords: 0,
    speakerWords: {}
};

const timerDisplay = document.getElementById("duration");

function calculateProgress(speakerWords, totalWords) {
    return totalWords > 0 ? (speakerWords / totalWords) * 100 : 0;
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function updateStatsDisplay(stats) {
    // Update the main stats
    document.getElementById('duration').textContent = formatTime(stats.duration);
    document.getElementById('processingTime').textContent = formatTime(stats.processingTime);
    document.getElementById('totalWords').textContent = stats.totalWords;

    // Update progress bars
    document.getElementById('processingProgress').style.width = `${calculateProgress(stats.processingTime, stats.duration)}%`;
    document.getElementById('durationProgress').style.width = `100%`;

    // Update speaker stats and progress
    for (let speaker in stats.speakerWords) {
        const speakerWordCount = document.getElementById(`speaker${speaker}Words`);
        if (speakerWordCount) {
            speakerWordCount.textContent = stats.speakerWords[speaker];
        }
        const speakerProgress = document.getElementById(`speaker${speaker}Progress`);
        if (speakerProgress) {
            speakerProgress.style.width = `${calculateProgress(stats.speakerWords[speaker], stats.totalWords)}%`;
        }
    }
}

function setupSpeechRecognition(speakerId) {
    // Check if the browser supports speech recognition
    if ('webkitSpeechRecognition' in window) {
        const recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        let startTime = Date.now();

        // Define the onresult event handler for speech recognition
        recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0].transcript)
                .join('');

            // Get the correct transcriptDiv for the speaker
            const transcriptDiv = document.getElementById(`transcriptSpeaker${speakerId}`);

            // Update the transcript in the UI
            transcriptDiv.textContent = transcript;

            // Store the final transcript when it's complete
            if (event.results[event.results.length - 1].isFinal) {
                userAnswer = transcript; // Store the final transcription
                const wordCount = userAnswer.split(' ').length;
                stats.totalWords += wordCount;
                if (!stats.speakerWords[speakerId.toString()]) {
                    stats.speakerWords[speakerId.toString()] = 0;
                }
                speakers_transcription.push(`Speaker${speakerId.toString()}: ${userAnswer}`)

                stats.speakerWords[speakerId.toString()] += wordCount;
                console.log(stats.totalWords)
                console.log(stats.speakerWords[speakerId.toString()])
                console.log(stats.speakerWords)
                    // Update processing time
                let processEndTime = Date.now();
                stats.processingTime = (processEndTime - startTime) / 1000;
                // Calculate total duration (total transcription duration)
                stats.duration += stats.processingTime
                    // Update the stats display
                updateStatsDisplay(stats);

            }
        };

        // Handle any errors with speech recognition
        recognition.onerror = (event) => {
            console.error("Speech Recognition Error:", event.error);
            alert("Error with speech recognition: " + event.error);
        };

        // Return the recognition object to start/stop as needed
        return recognition;
    } else {
        alert("Your browser does not support Speech Recognition");
        return null;
    }
}

function startRecording(speakerId) {
    if (!isRecording) {
        recognition = setupSpeechRecognition(speakerId)
        recognition.start();
        isRecording = true;
        updateStatsDisplay(stats);
        document.getElementById(`statusSpeaker${speakerId}`).textContent = "Recording...";
    }
}

function stopRecording(speakerId) {
    recognition.stop();
    isRecording = false;
    document.getElementById(`statusSpeaker${speakerId}`).textContent = "Recording stopped.";
}


document.getElementById("generateSpeakers").addEventListener("click", () => {
    const numSpeakers = document.getElementById("numSpeakers").value;
    const speakersContainer = document.getElementById("speakersContainer");
    const speakerDistributionContainer = document.getElementById("speakerDistribution");
    speakersContainer.innerHTML = "";

    speakerDistributionContainer.innerHTML = "";
    for (let i = 1; i <= numSpeakers; i++) {
        const speakerDiv = document.createElement("div");
        speakerDiv.classList.add("speaker-section");

        const speakerLabel = document.createElement("h3");
        speakerLabel.innerText = `Speaker ${i}`;


        const startBtn = document.createElement("button");
        startBtn.innerText = "Start Recording";
        startBtn.classList.add("startRecording");
        startBtn.onclick = () => startRecording(i);

        // const speakerMessage = document.createElement('p');
        // speakerMessage.innerHTML = `Say <strong style="color: red;">stop listening</strong> to stop the recording`;

        const stopBtn = document.createElement("button");
        stopBtn.innerText = "Stop Recording";
        stopBtn.classList.add("stopRecording");
        stopBtn.onclick = () => stopRecording(i);

        const statusDiv = document.createElement("div");
        statusDiv.id = `statusSpeaker${i}`;
        statusDiv.classList.add("status");

        const transcriptDiv = document.createElement("div");
        transcriptDiv.id = `transcriptSpeaker${i}`;
        transcriptDiv.classList.add("transcript");

        speakerDiv.appendChild(speakerLabel);
        speakerDiv.appendChild(startBtn);
        speakerDiv.appendChild(stopBtn);
        //speakerDiv.appendChild(speakerMessage);
        speakerDiv.appendChild(statusDiv);
        speakerDiv.appendChild(transcriptDiv);
        speakersContainer.appendChild(speakerDiv);

        // Generate Speaker Distribution Elements
        const statItemDiv = document.createElement("div");
        statItemDiv.classList.add("stat-item");

        const label = document.createElement("label");
        label.innerText = `Speaker ${i}: `;

        const wordCountSpan = document.createElement("span");
        wordCountSpan.id = `speaker${i}Words`;
        wordCountSpan.textContent = "0";

        const progressBar = document.createElement("div");
        progressBar.classList.add("progress-bar");

        const progress = document.createElement("div");
        progress.id = `speaker${i}Progress`;
        progress.classList.add("progress");
        progress.style.width = "0%";

        progressBar.appendChild(progress);
        statItemDiv.appendChild(label);
        statItemDiv.appendChild(wordCountSpan);
        statItemDiv.appendChild(document.createTextNode(" words"));
        statItemDiv.appendChild(progressBar);

        speakerDistributionContainer.appendChild(statItemDiv);
    }
});


// Text-to-Speech process handler
async function handleTextToSpeech() {
    const text = document.getElementById('textInput').value;
    if (!text) return;

    // Initial stats update with text length only
    const ttsStats = { textLength: 0, processingTime: 0, audioDuration: 0 };
    updateTTSStatsDisplay(ttsStats);

    try {
        const response = await fetch('/text-to-speech', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, stats, speakers_transcription })
        });

        const data = await response.json();

        if (data.audio) {
            // Update the audio element with the new audio
            const audio = document.getElementById('audioPlayer');
            audio.src = `data:audio/wav;base64,${data.audio}`;
            audio.style.display = 'block';
            statsData = data.stats;
            updateTTSStatsDisplay(statsData);

        }
    } catch (error) {
        console.error('Error:', error);
    }
}
document.getElementById('convertToSpeech').addEventListener('click', handleTextToSpeech);

// Utility function to format time in mm:ss
function formatTimetts(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
}

// Calculate progress for processing time based on audio duration
function calculateProgresstts(processingTime, audioDuration) {
    return audioDuration > 0 ? (processingTime / audioDuration) * 100 : 0;
}

// Function to update TTS stats display in the UI
function updateTTSStatsDisplay(ttsStats) {
    document.getElementById('textLength').textContent = `${ttsStats.total_words || ttsStats.textLength} words`;
    document.getElementById('ttsProcessingTime').textContent = formatTime(ttsStats.processing_time || 0);
    document.getElementById('audioDuration').textContent = formatTime(ttsStats.total_duration || 0);

    // Update progress bars
    document.getElementById('ttsProcessingProgress').style.width = `${calculateProgress(ttsStats.processing_time, ttsStats.total_duration)}%`;
    document.getElementById('audioDurationProgress').style.width = `100%`; // Full width for audio duration as it's static
}

// document.getElementById("saveToS3").addEventListener("click", async() => {
//     try {
//         const response = await fetch("/save-transcription-to-s3", {
//             method: "POST",
//             headers: {
//                 "Content-Type": "application/json"
//             }
//         });

//         if (response.ok) {
//             alert("Transcription saved to S3 successfully!");
//         } else {
//             alert("Failed to save transcription to S3.");
//         }
//     } catch (error) {
//         console.error("Error saving to S3:", error);
//         alert("An error occurred while saving to S3.");
//     }
// });