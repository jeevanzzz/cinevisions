document.addEventListener("DOMContentLoaded", () => {
    /* ================= PRELOADER SKIP ON NAV CLICK ================= */
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.addEventListener('click', function (e) {
            // Only set for internal navigation
            if (this.hostname === window.location.hostname) {
                sessionStorage.setItem('skipPreloader', 'true');
            }
        });
    });

    /* ================= PRELOADER LOGIC ================= */
    const videoPreloader = document.getElementById("video-preloader");
    const main = document.getElementById("main-content");
    const skipPreloader = sessionStorage.getItem('skipPreloader');

    // Portfolio init helper (if present)
    function safeInitPortfolio() {
        if (typeof initPortfolio === 'function') {
            initPortfolio();
        }
    }

    if (videoPreloader && main) {
        if (skipPreloader) {
            videoPreloader.style.display = "none";
            main.style.display = "block";
            sessionStorage.removeItem('skipPreloader');
            safeInitPortfolio();
        } else {
            main.style.display = "none";
            const preloaderVideo = videoPreloader.querySelector('video');
            if (preloaderVideo) {
                preloaderVideo.currentTime = 0;
                // Attempt to play
                const playPromise = preloaderVideo.play();

                if (playPromise !== undefined) {
                    playPromise.then(_ => {
                        // Autoplay started!
                    }).catch(error => {
                        // Autoplay was prevented. Fallback to timer.
                        console.log("Autoplay prevented:", error);
                        setTimeout(() => {
                            videoPreloader.style.opacity = "0";
                            setTimeout(() => {
                                videoPreloader.style.display = "none";
                                main.style.display = "block";
                                safeInitPortfolio();
                            }, 500);
                        }, 3000); // Wait 3 seconds then hide
                    });
                }

                preloaderVideo.onended = () => {
                    videoPreloader.style.opacity = "0";
                    setTimeout(() => {
                        videoPreloader.style.display = "none";
                        main.style.display = "block";
                        safeInitPortfolio();
                    }, 500);
                };
            } else {
                // fallback if no video element
                setTimeout(() => {
                    videoPreloader.style.opacity = "0";
                    setTimeout(() => {
                        videoPreloader.style.display = "none";
                        main.style.display = "block";
                        safeInitPortfolio();
                    }, 500);
                }, 3000);
            }
        }
    } else if (main) {
        if (videoPreloader) videoPreloader.style.display = "none";
        main.style.display = "block";
        safeInitPortfolio();
    }

    /* ================= AOS INIT ================= */
    if (window.AOS) {
        AOS.init({
            duration: 1000,
            once: true
        });
    }

    /* ================= NAVBAR SCROLL ================= */
    const navbar = document.querySelector(".navbar");
    if (navbar) {
        window.addEventListener("scroll", () => {
            navbar.classList.toggle("scrolled", window.scrollY > 50);
        });
    }

    /* ================= IMAGE LIGHTBOX ================= */
    const lightbox = document.getElementById("lightbox");
    const lightboxImg = document.querySelector(".lightbox-img");

    if (lightbox && lightboxImg) {
        document.addEventListener("click", e => {
            if (e.target.matches(".portfolio-media img")) {
                lightbox.style.display = "flex";
                lightboxImg.src = e.target.src;
            }
            if (e.target.classList.contains("close-lightbox")) {
                lightbox.style.display = "none";
            }
        });
    }

    /* ================= VIDEO LIGHTBOX ================= */
    document.querySelectorAll('.video-preview').forEach(card => {
        card.addEventListener('click', () => {
            const videoSrc = card.dataset.video;
            const videoBox = document.getElementById('videoLightbox');
            const video = document.getElementById('lightboxVideo');

            if (videoBox && video) {
                video.src = videoSrc;
                videoBox.style.display = 'flex';
                video.play();
            }
        });
    });

    const closeVideoBtn = document.querySelector('.close-video');
    if (closeVideoBtn) {
        closeVideoBtn.addEventListener('click', () => {
            const videoBox = document.getElementById('videoLightbox');
            const video = document.getElementById('lightboxVideo');
            if (videoBox) videoBox.style.display = 'none';
            if (video) {
                video.pause();
                video.currentTime = 0;
            }
        });
    }

    /* ================= FEATURE VIDEO PLAY (HOME) ================= */
    const featVideo = document.getElementById("featureVideo");
    const playBtn = document.getElementById("customPlayBtn");

    if (featVideo && playBtn) {
        featVideo.muted = true;
        featVideo.play().catch(() => { });

        playBtn.addEventListener("click", () => {
            featVideo.muted = false;
            featVideo.loop = false;
            featVideo.controls = true;
            featVideo.play();
            playBtn.style.display = "none";
        });

        featVideo.addEventListener("pause", () => {
            playBtn.style.display = "flex";
        });
    }

    /* ================= INSTA SCROLL (HOME) ================= */
    const instaSlider = document.querySelector(".insta-scroll");
    if (instaSlider) {
        let autoScroll = setInterval(() => {
            instaSlider.scrollLeft += 1;
            if (instaSlider.scrollLeft >= instaSlider.scrollWidth - instaSlider.clientWidth) {
                instaSlider.scrollLeft = 0;
            }
        }, 25);

        instaSlider.addEventListener("mouseenter", () => clearInterval(autoScroll));
        instaSlider.addEventListener("mouseleave", () => {
            autoScroll = setInterval(() => {
                instaSlider.scrollLeft += 1;
                if (instaSlider.scrollLeft >= instaSlider.scrollWidth - instaSlider.clientWidth) {
                    instaSlider.scrollLeft = 0;
                }
            }, 25);
        });
    }

    /* ================= DYNAMIC SCROLL BUTTON (Single Button) ================= */
    const toggleScrollBtn = document.getElementById("toggleScrollBtn");
    const toggleIcon = toggleScrollBtn ? toggleScrollBtn.querySelector("i") : null;

    function handleScrollParams() {
        if (!toggleScrollBtn || !toggleIcon) return;

        const scrollY = window.scrollY;
        const windowHeight = window.innerHeight;
        const bodyHeight = document.body.offsetHeight;

        // Show button after scrolling down a bit
        if (scrollY > 300) {
            toggleScrollBtn.classList.add("show");
        } else {
            toggleScrollBtn.classList.remove("show");
        }

        // Check if near bottom
        const isAtBottom = (windowHeight + scrollY) >= (bodyHeight - 100);

        if (isAtBottom) {
            // We are at bottom -> Show UP arrow -> Click goes to TOP
            toggleIcon.classList.remove("fa-arrow-down");
            toggleIcon.classList.add("fa-arrow-up");
            toggleScrollBtn.setAttribute("aria-label", "Scroll to top");
        } else {
            // We are NOT at bottom -> Show DOWN arrow -> Click goes to BOTTOM
            toggleIcon.classList.remove("fa-arrow-up");
            toggleIcon.classList.add("fa-arrow-down");
            toggleScrollBtn.setAttribute("aria-label", "Scroll to bottom");
        }
    }

    if (toggleScrollBtn) {
        window.addEventListener("scroll", handleScrollParams);

        toggleScrollBtn.addEventListener("click", () => {
            const scrollY = window.scrollY;
            const windowHeight = window.innerHeight;
            const bodyHeight = document.body.offsetHeight;
            const isAtBottom = (windowHeight + scrollY) >= (bodyHeight - 100);

            if (isAtBottom) {
                // Go to Top
                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });
            } else {
                // Scroll Down by one screen (Page Down feeling) instead of jumping to footer
                window.scrollBy({
                    top: window.innerHeight,
                    behavior: "smooth"
                });
            }
        });
    }

    /* ================= EMOJI RATING ================= */
    const emojis = document.querySelectorAll('.emoji-rating span');
    const ratingInput = document.getElementById('ratingValue');

    if (emojis.length > 0 && ratingInput) {
        emojis.forEach(emoji => {
            emoji.addEventListener('click', () => {
                emojis.forEach(e => e.classList.remove('active'));
                emoji.classList.add('active');
                ratingInput.value = emoji.dataset.value;
            });
        });
    }
});

/* ================= SERVICE TAB SWITCHING ================= */
function showService(serviceId, btn) {
    // 1. Hide all service sections
    document.querySelectorAll('.service-box').forEach(box => {
        box.classList.remove('active');
    });

    // 2. Remove active from all buttons
    document.querySelectorAll('.service-tab').forEach(button => {
        button.classList.remove('active');
    });

    // 3. Show selected service
    const target = document.getElementById(serviceId);
    if (target) {
        target.classList.add('active');
    }

    // 4. Activate clicked button
    if (btn) btn.classList.add('active');
}

/* ================= PORTFOLIO: DRAG + AUTO SCROLL ================= */
function initPortfolio() {
    const slider = document.querySelector(".portfolio-scroll");
    if (!slider) return;

    let isDragging = false;
    let startX = 0;
    let startScroll = 0;
    let autoScrollTimer = null;

    slider.addEventListener("mousedown", e => {
        isDragging = true;
        startX = e.pageX;
        startScroll = slider.scrollLeft;
    });

    window.addEventListener("mouseup", () => {
        isDragging = false;
    });

    slider.addEventListener("mousemove", e => {
        if (!isDragging) return;
        e.preventDefault();
        const delta = e.pageX - startX;
        slider.scrollLeft = startScroll - delta * 1.5;
    });

    function startAutoScroll() {
        stopAutoScroll();
        autoScrollTimer = setInterval(() => {
            slider.scrollLeft += 1;
            if (slider.scrollLeft >= slider.scrollWidth - slider.clientWidth) {
                slider.scrollLeft = 0;
            }
        }, 20);
    }

    function stopAutoScroll() {
        if (autoScrollTimer) {
            clearInterval(autoScrollTimer);
            autoScrollTimer = null;
        }
    }

    requestAnimationFrame(() => {
        startAutoScroll();
    });

    slider.addEventListener("mouseenter", stopAutoScroll);
    slider.addEventListener("mouseleave", startAutoScroll);
}
