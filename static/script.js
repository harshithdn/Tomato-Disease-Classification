
$(document).ready(function () {
  // === Element References ===
  const dropArea = document.querySelector("#drop-area");
  const uploadButton = document.querySelector("#uploadButton");
  const input = document.querySelector("#fileElement");
  const video = document.getElementById("camera");
  const languageSelect = document.getElementById("languageSelect");
  const speakButton = document.getElementById("speakButton");

  let file = null;
  let liveInterval = null;
  let stream = null;
  let currentLang = "en";
  let lastDescription = []; // stored as array of points

  // === Multilingual Texts ===
  const translations = {
    en: {
      title: "Tomato Disease Classification",
      subtitle: "Upload or capture an image of a tomato leaf to predict disease.",
      upload: "Upload Image",
      drag: "Drag & Drop your image here",
      filetype: "You can upload png, jpg, jpeg, webp or bmp images",
      result: "Result:",
      confidence: "Confidence score:",
      description: "Description:",
      speak: "🔊 Speak Description",
      footer: "All rights reserved",
      invalidFile: "Invalid file format! Please upload a valid image.",
      uploadError: "Error occurred while uploading.",
      cameraError: "Cannot access camera!"
    },
    kn: {
      title: "ಟೊಮ್ಯಾಟೊ ರೋಗ ವರ್ಗೀಕರಣ",
      subtitle: "ಟೊಮ್ಯಾಟೊ ಎಲೆಯ ಚಿತ್ರವನ್ನು ಅಪ್‌ಲೋಡ್ ಅಥವಾ ಹಿಡಿದು ರೋಗವನ್ನು ಪತ್ತೆಹಚ್ಚಿ.",
      upload: "ಚಿತ್ರವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
      startLive: "ಲೈವ್ ಪತ್ತೆ ಪ್ರಾರಂಭಿಸಿ",
      stopLive: "ಲೈವ್ ಪತ್ತೆ ನಿಲ್ಲಿಸಿ",
      drag: "ಚಿತ್ರವನ್ನು ಇಲ್ಲಿ ಎಳೆದು ಬಿಡಿ",
      filetype: "png, jpg, jpeg, webp ಅಥವಾ bmp ಚಿತ್ರಗಳನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಬಹುದು",
      result: "ಫಲಿತಾಂಶ:",
      confidence: "ನಂಬಿಕೆ ಅಂಕೆ:",
      description: "ವಿವರಣೆ:",
      speak: "🔊 ವಿವರಣೆಯನ್ನು ಓದಿ",
      footer: "ಎಲ್ಲ ಹಕ್ಕುಗಳು ಕಾಯ್ದಿರಿಸಲಾಗಿದೆ",
      invalidFile: "ಅಮಾನ್ಯ ಫೈಲ್! ಮಾನ್ಯ ಚಿತ್ರವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
      uploadError: "ಅಪ್‌ಲೋಡ್ ಮಾಡುವಾಗ ದೋಷ ಸಂಭವಿಸಿದೆ.",
      cameraError: "ಕ್ಯಾಮೆರಾವನ್ನು ಪ್ರವೇಶಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ!"
    },
    te: {
      title: "టమోటా వ్యాధి వర్గీకరణ",
      subtitle: "టమోటా ఆకు చిత్రాన్ని అప్‌లోడ్ చేయండి లేదా పట్టుకోండి వ్యాధిని గుర్తించండి.",
      upload: "చిత్రాన్ని అప్‌లోడ్ చేయండి",
      startLive: "ప్రత్యక్ష గుర్తింపు ప్రారంభించండి",
      stopLive: "ప్రత్యక్ష గుర్తింపును ఆపండి",
      drag: "చిత్రాన్ని ఇక్కడకి లాగి వదలండి",
      filetype: "png, jpg, jpeg, webp లేదా bmp చిత్రాలను అప్‌లోడ్ చేయవచ్చు",
      result: "ఫలితం:",
      confidence: "నమ్మక స్కోరు:",
      description: "వివరణ:",
      speak: "🔊 వివరణను చదవండి",
      footer: "అన్ని హక్కులు కాపాడబడ్డాయి",
      invalidFile: "చెల్లని ఫైల్! సరైన చిత్రాన్ని అప్‌లోడ్ చేయండి.",
      uploadError: "అప్‌లోడ్ చేస్తూ లోపం సంభవించింది.",
      cameraError: "కెమెరా యాక్సెస్ చేయలేకపోతున్నాం!"
    },
    hi: {
      title: "टमाटर रोग वर्गीकरण",
      subtitle: "टमाटर की पत्ती की छवि अपलोड करें या कैप्चर करें रोग की पहचान के लिए।",
      upload: "छवि अपलोड करें",
      startLive: "लाइव पहचान शुरू करें",
      stopLive: "लाइव पहचान रोकें",
      drag: "अपनी छवि यहाँ खींचें और छोड़ें",
      filetype: "png, jpg, jpeg, webp या bmp छवियाँ अपलोड करें",
      result: "परिणाम:",
      confidence: "विश्वास स्कोर:",
      description: "विवरण:",
      speak: "🔊 विवरण पढ़ें",
      footer: "सर्वाधिकार सुरक्षित",
      invalidFile: "अमान्य फ़ाइल! कृपया मान्य छवि अपलोड करें।",
      uploadError: "अपलोड के दौरान त्रुटि हुई।",
      cameraError: "कैमरा एक्सेस नहीं किया जा सका!"
    },
    ta: {
      title: "தக்காளி நோய் வகைப்படுத்தல்",
      subtitle: "தக்காளி இலை படத்தை பதிவேற்றவோ அல்லது பிடிக்கவோ செய்யுங்கள் நோயை கண்டறிய.",
      upload: "படத்தை பதிவேற்றவும்",
      startLive: "நேரடி கண்டறிதலை தொடங்கு",
      stopLive: "நேரடி கண்டறிதலை நிறுத்து",
      drag: "படத்தை இங்கே இழுத்து விடவும்",
      filetype: "png, jpg, jpeg, webp அல்லது bmp படங்களை பதிவேற்றலாம்",
      result: "விளைவு:",
      confidence: "நம்பிக்கை மதிப்பு:",
      description: "விளக்கம்:",
      speak: "🔊 விளக்கத்தை வாசிக்கவும்",
      footer: "அனைத்து உரிமைகளும் பாதுகாக்கப்பட்டுள்ளன",
      invalidFile: "தவறான கோப்பு! சரியான படத்தை பதிவேற்றவும்.",
      uploadError: "பதிவேற்றும் போது பிழை ஏற்பட்டது.",
      cameraError: "கேமராவை அணுக முடியவில்லை!"
    }
  };

  // Disease translations dictionary (frontend labels)
  const diseaseTranslations = {
    "Tomato Mosaic Virus": { en: "Tomato Mosaic Virus", hi: "[translate:टमाटर मोज़ेक वायरस]", kn: "[translate:ಟೊಮ್ಯಾಟೊ ಮೋಸೈಕ್ ವೈರಸ್]", te: "[translate:టమోటా మోజాయిక్ వైరస్]", ta: "[translate:தக்காளி மோசைக் வைரஸ்]" },
    "Target Spot": { en: "Target Spot", hi: "[translate:लक्ष्य धब्बा]", kn: "[translate:ಲಕ್ಷ್ಯ ದಾಗೆ]", te: "[translate:లక్ష్య బిందువు]", ta: "[translate:இலக்கு தழுவல்]" },
    "Bacterial Spot": { en: "Bacterial Spot", hi: "[translate:बैक्टीरियल स्पॉट]", kn: "[translate:ಜೀವಾಣು ಕಲೆ]", te: "[translate:బాక్టీరియల్ మచ్చ]", ta: "[translate:பாக்டீரியல் புள்ளி]" },
    "Early Blight": { en: "Early Blight", hi: "[translate:प्रारंभिक जलन]", kn: "[translate:ಆರಂಭಿಕ ಸುಟ್ಟುಹೋಗುವಿಕೆ]", te: "[translate:ప్రాథమిక చిటుపు]", ta: "[translate:ஆரம்ப இரும்பு]" },
    "Late Blight": { en: "Late Blight", hi: "[translate:देर से जलन]", kn: "[translate:ನಂತರದ ಸುಟ್ಟುಹೋಗುವುದು]", te: "[translate:సమయానంతరం బ్లైట్]", ta: "[translate:தாமதமான நாசம்]" },
    "Leaf Mold": { en: "Leaf Mold", hi: "[translate:पत्ती फफूंदी]", kn: "[translate:ಎಲೆ ಫಂಗೆಸ್]", te: "[translate:ఆకు దడ]", ta: "[translate:இலை பூஞ்சை]" },
    "Septoria Leaf Spot": { en: "Septoria Leaf Spot", hi: "[translate:सेप्टोरिया पत्ती धब्बा]", kn: "[translate:ಸೆಪ್ಟೋರಿಯಾ ಎಲೆ ಕಲೆ]", te: "[translate:సెప్టోరియా ఆకు మచ్చ]", ta: "[translate:செப்டோரியா இலைக் கீற்று]" },
    "Spider Mites": { en: "Spider Mites", hi: "[translate:मकड़ी के फंदे कीट]", kn: "[translate:ಚೆಳ್ಳಿ ಕೀಟಗಳು]", te: "[translate:సపారు పురుగు]", ta: "[translate:சிலந்தி பூச்சிகள்]" },
    "Bacterial Speck": { en: "Bacterial Speck", hi: "[translate:बैक्टीरियल स्पेक]", kn: "[translate:ಬ್ಯಾಕ್ಟೀರಿಯಾದ ಸ್ಪೆಕ್]", te: "[translate:బాక్టీరియల్ స్పెక్]", ta: "[translate:பாக்டீரியல் சிறுநீர்]" },
    "Healthy": { en: "Healthy", hi: "[translate:स्वस्थ]", kn: "[translate:ಆರೋಗ್ಯಕರ]", te: "[translate:ఆరోగ్యకరంగా]", ta: "[translate:ஆரோக்கியம்]" }
  };

  // === Update UI Language ===
  function updateLanguage(lang) {
    const t = translations[lang] || translations.en;
    $("#pageTitle").text(t.title);
    $("#pageSubtitle").text(t.subtitle);
    $("#uploadButton").text(t.upload);

    // live detection button text depends on state

    $("#dragText").text(t.drag);
    $("#fileTypeText").text(t.filetype);
    $("#resultLabel").text(t.result);
    $("#confidenceLabel").text(t.confidence);
    $("#descriptionLabel").text(t.description);
    $("#speakButton").text(t.speak);
    $("#footerText").text(t.footer);
  }

  // apply language change to the whole page including about/contact content
  async function applyLanguageToPage(lang) {
    updateLanguage(lang);

    // if on about/contact pages, ask backend for content
    const pageId = $("body").data("page"); // set data-page="about" or "contact" in templates
    if (pageId) {
      try {
        const res = await axios.post("/translate_content", { page: pageId, lang: lang });
        if (res.status === 200 && res.data && res.data.text) {
          // If the content is markdown-like (mail link), safely render innerHTML for that small piece
          $("#pageContent").html(res.data.text);
        }
      } catch (e) {
        console.error("Translate content error", e);
      }
    }
  }

  languageSelect.addEventListener("change", (e) => {
    currentLang = e.target.value;
    applyLanguageToPage(currentLang);
  });

  // === Live Detection ===

  // === Capture & Send Frame ===
  function captureAndSendFrame() {
    if (!video.srcObject) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 320;
    canvas.height = video.videoHeight || 240;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(blob => {
      file = new File([blob], "capture.jpg", { type: "image/jpeg" });
      showPreview(file);
      sendImage(file);
    }, "image/jpeg", 0.9);
  }

  // === File upload / Drag & Drop handlers ===
  uploadButton.onclick = () => input.click();
  input.onchange = () => handleFile(input.files[0]);
  dropArea.addEventListener("dragover", e => { e.preventDefault(); dropArea.classList.add("active"); });
  dropArea.addEventListener("dragleave", () => dropArea.classList.remove("active"));
  dropArea.addEventListener("drop", e => {
    e.preventDefault();
    dropArea.classList.remove("active");
    handleFile(e.dataTransfer.files[0]);
  });

  function handleFile(f) {
    if (!f) return;
    file = f;
    showPreview(file);
    sendImage(file);
  }

  // === Show Preview ===
  function showPreview(file) {
    const validTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp"];
    if (!validTypes.includes(file.type)) {
      toastr.error(translations[currentLang].invalidFile);
      return;
    }
    const reader = new FileReader();
    reader.onload = e => $("#previewImage").attr("src", e.target.result);
    reader.readAsDataURL(file);
  }

  // === Send image to backend and handle response ===
  async function sendImage(file) {
    const formData = new FormData();
    formData.append("file", file);

    $(".loadingArea").show();
    $(".resultArea").hide();

    try {
      const res = await axios.post("/predict", formData);
      $(".loadingArea").hide();

      if (res.status === 200 && res.data) {
        const label = res.data.label || "Unknown";
        const confidence = res.data["confidence score"] || "N/A";

        // Translate disease name for display (frontend dictionary)
        const translatedLabel = (diseaseTranslations[label] && diseaseTranslations[label][currentLang]) ? diseaseTranslations[label][currentLang] : label;
        $("#result").text(translatedLabel);
        $("#confidenceScore").text(confidence);

        // Fetch description (backend returns array of points)
        let description = [];
        try {
          const descRes = await axios.post("/describe", { disease: label, lang: currentLang });
          if (descRes.status === 200 && descRes.data && descRes.data.description) {
            description = descRes.data.description;
            lastDescription = Array.isArray(description) ? description : [description];
          }
        } catch (err) {
          console.error(err);
        }

        // Render description as a numbered list
        if (Array.isArray(lastDescription) && lastDescription.length) {
          const listHtml = lastDescription.map(pt => `<li>${escapeHtml(pt)}</li>`).join("");
          $("#diseaseDescription").html(`<ol>${listHtml}</ol>`);
        } else {
          $("#diseaseDescription").text("No description available");
        }

        $(".resultArea").fadeIn();
      } else {
        toastr.error(translations[currentLang].uploadError);
      }
    } catch (err) {
      $(".loadingArea").hide();
      toastr.error(translations[currentLang].uploadError);
    }
  }

  // escape HTML to avoid injection
  function escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // === Speak Description ===
  speakButton.addEventListener("click", async () => {
    if (!lastDescription || !lastDescription.length) {
      toastr.warning(translations[currentLang].description + " not available!");
      return;
    }
    try {
      // join points into a readable paragraph for speech
      const textToSpeak = lastDescription.join(". ");
      const response = await fetch("/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textToSpeak, lang: currentLang })
      });
      if (!response.ok) throw new Error("Speech generation failed!");
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.play();
    } catch (error) {
      console.error(error);
      toastr.error("Failed to play description voice!");
    }
  });

  // === Cancel / Reset upload ===
  $(".cancelUpload").click(() => {
    $("#previewImage").attr("src", "../static/images/drag_drop.svg");
    $(".loadingArea, .resultArea").hide();
    if (liveInterval) stopLiveDetection();
  });

  // Initialize page: set data-page-based content if present
  const pageId = $("body").data("page"); // add data-page to body in templates (e.g., data-page="about")
  if (pageId) {
    // load page-specific translated content
    applyLanguageToPage(currentLang);
  } else {
    updateLanguage(currentLang);
  }
});
