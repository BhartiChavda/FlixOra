// CineMood JavaScript Core - V3 Social
document.addEventListener("DOMContentLoaded", () => {
    // 1. Mobile Menu Toggle
    const menuToggle = document.getElementById("menuToggle");
    const navLinks = document.getElementById("navLinks");

    if (menuToggle && navLinks) {
        menuToggle.addEventListener("click", () => {
            navLinks.classList.toggle("active");
            
            const icon = menuToggle.querySelector("i");
            if (navLinks.classList.contains("active")) {
                icon.classList.remove("fa-bars");
                icon.classList.add("fa-xmark");
            } else {
                icon.classList.remove("fa-xmark");
                icon.classList.add("fa-bars");
            }
        });
    }

    // 1.5 Profile Dropdown Click Toggle
    const profileDropdown = document.getElementById("profileDropdown");
    const dropdownToggle = document.getElementById("dropdownToggle");
    if (profileDropdown && dropdownToggle) {
        dropdownToggle.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            profileDropdown.classList.toggle("show");
        });

        document.addEventListener("click", (e) => {
            if (!profileDropdown.contains(e.target)) {
                profileDropdown.classList.remove("show");
            }
        });
    }

    // 2. AJAX Media Type / Category Recommendation Filter
    const mediaTypeButtons = document.querySelectorAll(".mood-btn");
    const langButtons = document.querySelectorAll(".lang-btn");
    const moviesGrid = document.getElementById("moviesGrid");
    const dynamicSectionTitle = document.getElementById("dynamicSectionTitle");
    const trendingMoviesSection = document.getElementById("trendingMoviesSection");
    const aiRecommendationsSection = document.getElementById("aiRecommendationsSection");
 
    let activeMediaType = "";
    let activeLanguage = "";
    let searchQuery = "";

    const catalogSearchInput = document.getElementById("catalogSearchInput");
    if (catalogSearchInput) {
        let debounceTimer;
        catalogSearchInput.addEventListener("input", (e) => {
            searchQuery = e.target.value;
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                fetchFilteredContent();
            }, 300);
        });
    }

    async function fetchFilteredContent() {
        if (!moviesGrid) return;
        moviesGrid.style.opacity = "0.3";
        moviesGrid.style.transition = "opacity 0.2s ease";
 
        try {
            const response = await fetch(`/recommend/?media_type=${activeMediaType}&language=${activeLanguage}&q=${encodeURIComponent(searchQuery)}&ajax=true`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
 
            if (!response.ok) throw new Error("Network response failed");
            const data = await response.json();
            
            // Get active category button's label for the empty message
            const activeBtn = document.querySelector(".mood-btn.active");
            const mediaLabel = activeBtn ? activeBtn.innerText.trim() : "this category";
            renderMovieCards(data.movies, mediaLabel);
 
        } catch (error) {
            console.error("Error fetching suggestions:", error);
            moviesGrid.innerHTML = `
                <div class="no-movies-error" style="grid-column: 1/-1; text-align: center; padding: 3rem;">
                    <i class="fa-solid fa-triangle-exclamation" style="font-size: 3rem; color: var(--neon-pink); text-shadow: var(--glow-pink); margin-bottom: 1rem;"></i>
                    <p style="font-size: 1.1rem; color: var(--text-dim);">Unable to fetch recommendations right now. Try again later!</p>
                </div>
            `;
        } finally {
            moviesGrid.style.opacity = "1";
        }
    }

    if (mediaTypeButtons.length > 0 && moviesGrid) {
        mediaTypeButtons.forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                
                activeMediaType = btn.getAttribute("data-media-type") || "";
                
                mediaTypeButtons.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
 
                // Hide or show Trending and AI Recommendation rows based on the selected category
                if (activeMediaType === "") {
                    if (trendingMoviesSection) trendingMoviesSection.style.display = "block";
                    if (aiRecommendationsSection) aiRecommendationsSection.style.display = "block";
                } else {
                    if (trendingMoviesSection) trendingMoviesSection.style.display = "none";
                    if (aiRecommendationsSection) aiRecommendationsSection.style.display = "none";
                }
 
                if (dynamicSectionTitle) {
                    const label = btn.innerText.trim();
                    dynamicSectionTitle.innerHTML = `Explore <span style="color: var(--neon-cyan); text-shadow: var(--glow-cyan);">${label}</span>`;
                }
 
                fetchFilteredContent();
            });
        });
    }

    if (langButtons.length > 0) {
        langButtons.forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                
                activeLanguage = btn.getAttribute("data-lang") || "";
                
                langButtons.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                
                fetchFilteredContent();
            });
        });
    }
 
    // Render helper function for dynamic movie grid cards
    function renderMovieCards(movies, mediaLabel) {
        if (!moviesGrid) return;
        moviesGrid.innerHTML = "";
        
        if (movies.length === 0) {
            moviesGrid.innerHTML = `
                <div class="no-movies" style="grid-column: 1/-1; text-align: center; padding: 4rem 2rem; background: var(--bg-card); border-radius: 24px; border: 1px dashed var(--border-glass);">
                    <i class="fa-solid fa-ghost" style="font-size: 3.5rem; color: var(--neon-purple); text-shadow: var(--glow-purple); margin-bottom: 1.2rem; display: block;"></i>
                    <h4 style="font-size: 1.3rem; font-weight: 800; text-transform: uppercase; margin-bottom: 0.5rem;">No Matches Found</h4>
                    <p style="color: var(--text-dim); font-size: 0.95rem;">We couldn't find any content for the category "${mediaLabel}". Try adding one in the Add Movie section!</p>
                </div>
            `;
            return;
        }

        movies.forEach(movie => {
            let aiBadge = "";
            let avgVal = parseFloat(movie.avg_rating);
            if (isNaN(avgVal) || avgVal >= 7.0) {
                aiBadge = `<span class="ai-recommend ai-watch">WATCH 👍</span>`;
            } else {
                aiBadge = `<span class="ai-recommend ai-skip">SKIP 👎</span>`;
            }

            const cardHTML = `
                <div class="movie-card-container">
                    <div class="movie-card-inner">
                        <!-- Front of Card -->
                        <div class="movie-card-front">
                            <img src="${movie.poster_url}" alt="${movie.title}" class="card-poster" onerror="this.src='https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop'">
                            
                            <div class="card-badge-type">
                                ${movie.media_type_display}
                            </div>
                            
                            <div class="card-badge-rating">
                                <i class="fa-solid fa-star" style="color: var(--neon-yellow);"></i>
                                <span>${movie.avg_rating ? movie.avg_rating : 'N/A'}</span>
                            </div>
                            
                            <div class="card-front-overlay">
                                <h4 class="card-front-title">${movie.title}</h4>
                                <span class="card-front-meta">${movie.genre}</span>
                            </div>
                        </div>
                        
                        <!-- Back of Card -->
                        <div class="movie-card-back">
                            <h3 class="card-back-title">${movie.title}</h3>
                            <div class="card-back-meta" style="font-size: 0.75rem; margin-bottom: 0.3rem;">
                                <span>${movie.release_date}</span> • <span>${movie.genre}</span>
                            </div>
                            
                            <div style="font-size: 0.72rem; color: var(--neon-cyan); margin-bottom: 0.4rem; text-align: left; font-weight: 700; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 3px; width: 100%; text-overflow: ellipsis; white-space: nowrap; overflow: hidden;">
                                ${movie.cast_info || 'Cast details coming soon...'}
                            </div>
                            
                            <p class="card-back-desc" style="font-size: 0.8rem; margin-bottom: 0.5rem; line-height: 1.4;">${movie.description}</p>
                            
                            <div class="card-back-ai" style="margin-bottom: 0.8rem; padding: 0.4rem;">
                                <strong>AI Verdict:</strong> ${aiBadge}
                            </div>
                            
                            <div class="card-back-btn">
                                <a href="/movie/${movie.id}/" class="btn-neon form-btn-full" style="display: block; text-align: center; padding: 0.5rem;">
                                    <i class="fa-solid fa-comments"></i> View Details
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            moviesGrid.insertAdjacentHTML("beforeend", cardHTML);
        });
    }

    // 3. Overall Rating SVG Circle Animation
    const ratingCircle = document.querySelector('.circle-wrap svg circle.progress');
    const ratingValueSpan = document.getElementById('ratingValue');
    if (ratingCircle && ratingValueSpan) {
        const rating = parseFloat(ratingValueSpan.getAttribute('data-rating') || '0');
        const percentage = rating * 10;
        
        // Circumference of R=50 is 314
        const circumference = 314;
        ratingCircle.style.strokeDasharray = `${circumference}`;
        const offset = circumference - (percentage / 100) * circumference;
        
        // Delayed paint for smooth progress animation
        setTimeout(() => {
            ratingCircle.style.strokeDashoffset = offset;
        }, 150);
    }

    // 4. Trailer Modal Toggle
    const trailerBtn = document.getElementById("openTrailerBtn");
    const trailerModal = document.getElementById("trailerModal");
    const trailerClose = document.getElementById("closeTrailerBtn");
    const trailerIframe = document.getElementById("trailerIframe");

    function getYoutubeEmbedUrl(url) {
        if (!url) return "";
        if (url.includes("/embed/")) {
            return url;
        }
        let regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
        let match = url.match(regExp);
        if (match && match[2].length === 11) {
            return "https://www.youtube.com/embed/" + match[2] + "?autoplay=1";
        }
        return url;
    }

    if (trailerBtn && trailerModal && trailerClose && trailerIframe) {
        trailerBtn.addEventListener("click", (e) => {
            e.preventDefault();
            const rawUrl = trailerBtn.getAttribute("data-trailer-url");
            if (rawUrl) {
                trailerIframe.src = getYoutubeEmbedUrl(rawUrl);
                trailerModal.classList.add("active");
            }
        });

        const closeModal = () => {
            trailerModal.classList.remove("active");
            trailerIframe.src = "";
        };

        trailerClose.addEventListener("click", closeModal);
        
        trailerModal.addEventListener("click", (e) => {
            if (e.target === trailerModal) {
                closeModal();
            }
        });
    }

    // 5. AJAX Review Likes reaction buttons (Delegated on body)
    document.body.addEventListener('click', async (e) => {
        const reactBtn = e.target.closest('.btn-react');
        if (!reactBtn) return;
        
        e.preventDefault();
        const reviewId = reactBtn.getAttribute('data-review-id');
        const commentId = reactBtn.getAttribute('data-comment-id');
        
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const formData = new FormData();
            if (reviewId) {
                formData.append('review_id', reviewId);
            }
            if (commentId) {
                formData.append('comment_id', commentId);
            }
            
            const response = await fetch(`/like/toggle/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                const countVal = data.count !== undefined ? data.count : data.total_likes;
                
                // Update count inside button
                const btnCount = reactBtn.querySelector('.count');
                if (btnCount) btnCount.innerText = countVal;
                
                // Update count in likes count row
                const containerCount = reactBtn.closest('.review-actions-container')?.querySelector('.likes-count-row .count');
                if (containerCount) containerCount.innerText = countVal;
                
                if (data.liked) {
                    reactBtn.classList.add('liked');
                } else {
                    reactBtn.classList.remove('liked');
                }
            }
        } catch (error) {
            console.error('Reaction request failed:', error);
        }
    });

    // AJAX Bookmark toggle (Delegated on body)
    document.body.addEventListener('click', async (e) => {
        const bookmarkBtn = e.target.closest('.btn-bookmark-icon');
        if (!bookmarkBtn) return;
        
        e.preventDefault();
        const reviewId = bookmarkBtn.getAttribute('data-review-id');
        if (!reviewId) return;
        
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const formData = new FormData();
            formData.append('review_id', reviewId);
            
            const response = await fetch(`/bookmark/toggle/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.saved) {
                    bookmarkBtn.classList.add('bookmarked');
                    if (typeof showToast === 'function') {
                        showToast('Review saved to your bookmarks!');
                    } else {
                        alert('Review saved to your bookmarks!');
                    }
                } else {
                    bookmarkBtn.classList.remove('bookmarked');
                    if (typeof showToast === 'function') {
                        showToast('Review removed from bookmarks.');
                    } else {
                        alert('Review removed from bookmarks.');
                    }
                }
            }
        } catch (error) {
            console.error('Bookmark request failed:', error);
        }
    });

    // Collapsible Filters Panel Logic (Shutable)
    const moodPanel = document.getElementById("moodPanel");
    const closeFiltersBtn = document.getElementById("closeFiltersBtn");
    const collapsedFiltersTrigger = document.getElementById("collapsedFiltersTrigger");
    const showFiltersBtn = document.querySelector(".show-filters-btn");

    if (moodPanel && closeFiltersBtn && collapsedFiltersTrigger && showFiltersBtn) {
        const setPanelState = (isCollapsed) => {
            if (isCollapsed) {
                moodPanel.classList.add("collapsed");
                setTimeout(() => {
                    if (moodPanel.classList.contains("collapsed")) {
                        moodPanel.style.display = "none";
                    }
                }, 400); // matches CSS transition duration
                collapsedFiltersTrigger.style.display = "flex";
                localStorage.setItem("filtersPanelCollapsed", "true");
            } else {
                moodPanel.style.display = "block";
                // Trigger reflow for transition to animate properly
                moodPanel.offsetHeight; 
                moodPanel.classList.remove("collapsed");
                collapsedFiltersTrigger.style.display = "none";
                localStorage.setItem("filtersPanelCollapsed", "false");
            }
        };

        // Load saved state (default to expanded 'false' if not set)
        const savedState = localStorage.getItem("filtersPanelCollapsed");
        if (savedState === "true") {
            moodPanel.style.transition = "none";
            moodPanel.classList.add("collapsed");
            moodPanel.style.display = "none";
            collapsedFiltersTrigger.style.display = "flex";
            setTimeout(() => {
                moodPanel.style.transition = "";
            }, 50);
        } else {
            moodPanel.style.display = "block";
            moodPanel.classList.remove("collapsed");
            collapsedFiltersTrigger.style.display = "none";
        }

        closeFiltersBtn.addEventListener("click", () => {
            setPanelState(true);
        });

        showFiltersBtn.addEventListener("click", () => {
            setPanelState(false);
        });
    }

    // Auto-dismiss messages toast alert
    const toasts = document.querySelectorAll(".toast");
    toasts.forEach(toast => {
        setTimeout(() => {
            toast.style.transform = "translateX(150%)";
            toast.style.opacity = "0";
            toast.style.transition = "all 0.5s ease";
            setTimeout(() => toast.remove(), 500);
        }, 5000);
    });

    // 6. AJAX Follow/Unfollow toggle
    document.body.addEventListener('click', async (e) => {
        const followBtn = e.target.closest('.btn-follow-toggle');
        if (!followBtn) return;
        
        e.preventDefault();
        const username = followBtn.getAttribute('data-username');
        if (!username) return;
        
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            if (!csrfToken) {
                console.error("CSRF token not found for follow AJAX action.");
                return;
            }
            
            const response = await fetch(`/user/${username}/follow/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Update stats counts on the page if they exist
                const followingCountEl = document.getElementById('currentUserFollowingCount');
                if (followingCountEl && data.followed !== undefined) {
                    let currentCount = parseInt(followingCountEl.innerText) || 0;
                    if (data.followed) {
                        followingCountEl.innerText = currentCount + 1;
                    } else {
                        followingCountEl.innerText = Math.max(0, currentCount - 1);
                    }
                }
                
                // Update all buttons targeting this same user
                const siblingButtons = document.querySelectorAll(`.btn-follow-toggle[data-username="${username}"]`);
                siblingButtons.forEach(btn => {
                    if (data.followed) {
                        btn.classList.add('active');
                        btn.innerText = 'Unfollow';
                    } else {
                        btn.classList.remove('active');
                        btn.innerText = 'Follow';
                    }
                });
                
                if (typeof showToast === 'function') {
                    showToast(data.followed ? `Now following @${username}!` : `Unfollowed @${username}.`);
                }
            }
        } catch (error) {
            console.error('Follow request failed:', error);
        }
    });

    // 7. AJAX Comment Submission (Replies / Publish)
    document.body.addEventListener('submit', async (e) => {
        const commentForm = e.target.closest('.ajax-comment-form');
        if (!commentForm) return;
        
        e.preventDefault();
        
        const actionUrl = commentForm.getAttribute('action');
        const formData = new FormData(commentForm);
        
        try {
            const response = await fetch(actionUrl, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Clear the input
                const textInput = commentForm.querySelector('input[name="text"]');
                if (textInput) {
                    textInput.value = '';
                }
                
                // If it is a nested reply, hide the form
                const parentIdInput = commentForm.querySelector('input[name="parent_id"]');
                if (parentIdInput) {
                    commentForm.style.display = 'none';
                }
                
                // Construct comment HTML
                let commentHtml = '';
                const verifiedIcon = data.user_verified ? ' <i class="fa-solid fa-circle-check verified-badge" style="color: var(--neon-yellow);"></i>' : '';
                
                if (parentIdInput) {
                    // It's a nested reply (Level 2)
                    commentHtml = `
                    <div class="comment-thread" style="margin-left: 1.2rem; margin-top: 0.6rem; border-left: 2px dashed rgba(255, 255, 255, 0.1); padding-left: 0.8rem;">
                        <div class="comment-box" style="background: rgba(255, 255, 255, 0.01); border: 1px solid rgba(255, 255, 255, 0.03); border-radius: 12px; padding: 0.8rem; margin-bottom: 0; color: #fff;">
                            <div class="comment-meta">
                                <a href="/user/${data.user}/" class="comment-username" style="color: var(--neon-cyan); font-weight: 700; text-decoration: none;">
                                    ${data.user}${verifiedIcon}
                                </a>
                                <span style="color: var(--text-dim); font-size: 0.75rem; margin-left: 5px;">• ${data.created_at}</span>
                            </div>
                            <p class="comment-text" style="color: #fff; font-size: 0.85rem; margin-top: 0.3rem;">${data.text}</p>
                        </div>
                    </div>`;
                    
                    commentForm.insertAdjacentHTML('afterend', commentHtml);
                } else {
                    // It's a root level comment
                    commentHtml = `
                    <div class="comment-box" style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 0.8rem; margin-bottom: 0.8rem; color: #fff;">
                        <div class="comment-meta">
                            <a href="/user/${data.user}/" class="comment-username" style="color: var(--neon-cyan); font-weight: 700; text-decoration: none;">
                                ${data.user}${verifiedIcon}
                            </a>
                            <span style="color: var(--text-dim); font-size: 0.75rem; margin-left: 5px;">• ${data.created_at}</span>
                        </div>
                        <p class="comment-text" style="color: #fff; font-size: 0.9rem; margin-top: 0.3rem;">${data.text}</p>
                        
                        <div class="comment-actions" style="margin-top: 0.5rem;">
                            <button class="comment-reply-btn" onclick="toggleReplyForm('reply-form-${data.id}')" style="background: none; border: none; color: var(--neon-cyan); font-size: 0.75rem; cursor: pointer; font-weight: 700;">
                                <i class="fa-solid fa-reply"></i> Reply
                            </button>
                        </div>

                        <form action="${actionUrl}" method="POST" id="reply-form-${data.id}" class="ajax-comment-form" style="display:none; margin-top: 0.6rem;">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${formData.get('csrfmiddlewaretoken')}">
                            <input type="hidden" name="parent_id" value="${data.id}">
                            <div style="display: flex; gap: 8px;">
                                <input type="text" name="text" placeholder="Write reply..." required style="flex: 1; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 0.3rem 0.6rem; font-size: 0.85rem; background: rgba(0, 0, 0, 0.25); color: #fff;">
                                <button type="submit" class="btn-neon" style="padding: 0.3rem 0.8rem; font-size: 0.75rem; border-color: var(--neon-cyan); box-shadow: var(--glow-cyan);">Reply</button>
                            </div>
                        </form>
                    </div>`;
                    
                    commentForm.insertAdjacentHTML('beforebegin', commentHtml);
                }
                
                if (typeof showToast === 'function') {
                    showToast('Comment published!');
                }
            }
        } catch (error) {
            console.error('Comment posting failed:', error);
        }
    });
});

// Global Connections Modal (Followers/Following) Dynamic Handlers
window.openConnectionsModal = async function(username, type) {
    const modal = document.getElementById('globalConnectionsModal');
    const title = document.getElementById('globalConnectionsTitle');
    const listContainer = document.getElementById('globalConnectionsList');
    
    if (!modal || !title || !listContainer) return;
    
    // Set title
    title.textContent = type === 'followers' ? 'Followers' : 'Following';
    
    // Clear list and show loader
    listContainer.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; padding: 3rem 0;">
            <i class="fa-solid fa-spinner fa-spin" style="font-size: 2rem; color: var(--neon-cyan);"></i>
        </div>
    `;
    
    // Show modal
    modal.style.display = 'flex';
    setTimeout(() => {
        modal.style.opacity = '1';
    }, 10);
    
    try {
        const response = await fetch(`/user/${username}/connections/json/?type=${type}`);
        if (response.ok) {
            const data = await response.json();
            const connections = data.connections || [];
            
            if (connections.length === 0) {
                listContainer.innerHTML = `
                    <div style="text-align: center; padding: 2rem 1rem; color: var(--text-dim);">
                        <p style="font-size: 0.9rem; margin: 0;">No ${type} yet.</p>
                    </div>
                `;
                return;
            }
            
            let listHtml = '';
            connections.forEach(conn => {
                const verifiedBadge = conn.verified ? ' <i class="fa-solid fa-circle-check verified-badge" style="color: var(--neon-yellow); font-size: 0.75rem; margin-left: 2px;"></i>' : '';
                const bioSnippet = conn.bio ? `<p style="font-size: 0.75rem; color: var(--text-dim); margin: 2px 0 0 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 180px;">${conn.bio}</p>` : '';
                
                let followBtnHtml = '';
                if (!conn.is_self) {
                    const activeClass = conn.is_following ? 'active' : '';
                    const btnStyle = conn.is_following 
                        ? 'background: none; border: 1px solid rgba(255, 255, 255, 0.15); color: var(--text-dim);' 
                        : 'background: none; border: 1px solid var(--neon-cyan); color: var(--neon-cyan);';
                    const btnLabel = conn.is_following ? 'Following' : 'Follow';
                    
                    followBtnHtml = `
                        <button class="btn-modal-follow-global ${activeClass}" data-username="${conn.username}" 
                            onclick="toggleGlobalModalFollow(this)" 
                            style="${btnStyle} padding: 0.35rem 0.9rem; border-radius: 10px; font-size: 0.72rem; font-weight: 800; cursor: pointer; transition: all 0.2s ease;">
                            ${btnLabel}
                        </button>
                    `;
                }
                
                listHtml += `
                    <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03); border-radius: 14px; padding: 0.6rem 0.8rem;">
                        <a href="/user/${conn.username}/" style="display: flex; align-items: center; gap: 0.8rem; text-decoration: none; color: #fff;">
                            <div style="width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, var(--neon-purple), var(--neon-pink)); display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 0.95rem; text-shadow: 0 0 5px rgba(255,255,255,0.5);">
                                ${conn.avatar_char}
                            </div>
                            <div style="text-align: left;">
                                <span style="font-weight: 700; font-size: 0.88rem; display: flex; align-items: center; gap: 4px;">
                                    ${conn.username}${verifiedBadge}
                                </span>
                                ${bioSnippet}
                            </div>
                        </a>
                        ${followBtnHtml}
                    </div>
                `;
            });
            
            listContainer.innerHTML = listHtml;
        } else {
            listContainer.innerHTML = `
                <div style="text-align: center; padding: 2rem 1rem; color: var(--neon-pink);">
                    <p style="font-size: 0.9rem; margin: 0;">Error loading connections.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching connections:', error);
        listContainer.innerHTML = `
            <div style="text-align: center; padding: 2rem 1rem; color: var(--neon-pink);">
                <p style="font-size: 0.9rem; margin: 0;">Error loading connections.</p>
            </div>
        `;
    }
};

window.closeGlobalConnectionsModal = function() {
    const modal = document.getElementById('globalConnectionsModal');
    if (!modal) return;
    modal.style.opacity = '0';
    setTimeout(() => {
        modal.style.display = 'none';
    }, 250);
};

window.toggleGlobalModalFollow = async function(btn) {
    const username = btn.getAttribute('data-username');
    if (!username) return;
    
    btn.disabled = true;
    
    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) {
            console.error("CSRF token not found for modal follow action.");
            return;
        }
        
        const response = await fetch(`/user/${username}/follow/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            const allBtns = document.querySelectorAll(`[data-username="${username}"]`);
            allBtns.forEach(el => {
                if (data.followed) {
                    el.classList.add('active');
                    el.style.borderColor = 'rgba(255, 255, 255, 0.15)';
                    el.style.color = 'var(--text-dim)';
                    el.innerText = 'Following';
                } else {
                    el.classList.remove('active');
                    el.style.borderColor = 'var(--neon-cyan)';
                    el.style.color = 'var(--neon-cyan)';
                    el.innerText = 'Follow';
                }
            });
            
            const followingCountSpan = document.getElementById('currentUserFollowingCount');
            if (followingCountSpan) {
                let currentVal = parseInt(followingCountSpan.innerText) || 0;
                if (data.followed) {
                    followingCountSpan.innerText = currentVal + 1;
                } else {
                    followingCountSpan.innerText = Math.max(0, currentVal - 1);
                }
            }
            
            const followersCount = document.getElementById('followersCount');
            const followingCount = document.getElementById('followingCount');
            if (followersCount && username === document.querySelector('.profile-username')?.textContent?.trim()) {
                followersCount.textContent = data.follower_count;
            }
            
            if (typeof showToast === 'function') {
                showToast(data.followed ? `Now following @${username}!` : `Unfollowed @${username}.`);
            }
        }
    } catch (e) {
        console.error('Modal follow action failed:', e);
    } finally {
        btn.disabled = false;
    }
};

// Close modal when clicking outside content area
document.addEventListener('click', (e) => {
    const modal = document.getElementById('globalConnectionsModal');
    if (e.target === modal) {
        closeGlobalConnectionsModal();
    }
});

// Global navigation helper
window.goBackOrRedirect = function(fallbackUrl) {
    if (document.referrer && document.referrer.includes(window.location.host)) {
        window.history.back();
    } else {
        window.location.href = fallbackUrl;
    }
};
