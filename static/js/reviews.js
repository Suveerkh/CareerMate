// reviews.js - Handles review functionality

document.addEventListener('DOMContentLoaded', function() {
    // Star rating functionality for displaying existing reviews
    const starRatings = document.querySelectorAll('.star-rating');
    starRatings.forEach(function(ratingContainer) {
        const stars = ratingContainer.querySelectorAll('.star');
        const ratingValue = parseInt(ratingContainer.dataset.rating);
        
        stars.forEach(function(star, index) {
            if (index < ratingValue) {
                star.classList.add('filled');
            }
        });
    });

    // Star rating functionality for the review form
    const ratingInputs = document.querySelectorAll('.rating-input input');
    ratingInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            document.getElementById('selected-rating').textContent = this.value;
        });
    });

    // Like button functionality
    const likeButtons = document.querySelectorAll('.like-button');
    likeButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const reviewId = this.dataset.reviewId;
            const likeCount = this.querySelector('.like-count');
            
            // Send AJAX request to like the review
            fetch('/like-review/' + reviewId, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update like count
                    likeCount.textContent = data.likes;
                    
                    // Toggle liked class
                    if (data.liked) {
                        button.classList.add('liked');
                    } else {
                        button.classList.remove('liked');
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });

    // Delete button functionality
    const deleteButtons = document.querySelectorAll('.delete-button');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            if (confirm('Are you sure you want to delete this review? This action cannot be undone.')) {
                const reviewId = this.dataset.reviewId;
                
                // Send AJAX request to delete the review
                fetch('/delete-review/' + reviewId, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Remove the review card from the DOM
                        const reviewCard = button.closest('.review-card');
                        reviewCard.remove();
                        
                        // If no reviews left, show the "no reviews" message
                        const reviewsSection = document.querySelector('.reviews-section');
                        const reviewCards = reviewsSection.querySelectorAll('.review-card');
                        if (reviewCards.length === 0) {
                            const noReviewsMessage = document.createElement('p');
                            noReviewsMessage.textContent = 'No reviews yet. Be the first to share your experience!';
                            reviewsSection.insertBefore(noReviewsMessage, reviewsSection.querySelector('.write-review-section'));
                        }
                    } else {
                        alert('Error deleting review: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while deleting your review. Please try again.');
                });
            }
        });
    });

    // Review form submission
    const reviewForm = document.getElementById('review-form');
    if (reviewForm) {
        reviewForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const degreePath = this.dataset.degreePath;
            
            fetch('/submit-review/' + degreePath, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Reload the page to show the new review
                    window.location.reload();
                } else {
                    alert('Error submitting review: ' + (data.message || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while submitting your review. Please try again. ' + error.message);
            });
        });
    }
});