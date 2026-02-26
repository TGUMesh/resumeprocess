document.getElementById('resumeForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const progressBar = document.getElementById('uploadProgress');
    const resultSection = document.getElementById('results');

    // Show loading state
    progressBar.style.display = 'block';
    resultSection.style.display = 'none';

    const formData = new FormData(this);
    console.log('Form data:', formData); // Debug log

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Received data:', data); // Debug log

            // Hide progress bar
            progressBar.style.display = 'none';

            // Show results panel
            resultSection.style.display = 'block';

            // Display extracted skills
            const skillsList = document.getElementById('skillsList');
            skillsList.innerHTML = '';

            if (data.skills && data.skills.length > 0) {
                data.skills.forEach(skill => {
                    if (skill && skill.trim()) {
                        const badge = document.createElement('span');
                        badge.className = 'inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium';
                        badge.textContent = skill.trim();
                        skillsList.appendChild(badge);
                    }
                });
            } else {
                skillsList.innerHTML = '<p class="text-gray-500">No skills extracted</p>';
            }

            const resumePreview = document.getElementById('resumePreview');
            resumePreview.style.display = 'block';

            const resumeIframe = document.getElementById('resumeIframe');
            resumeIframe.src = URL.createObjectURL(formData.get('resume'));
            resumeIframe.style.display = 'block';
            document.getElementById('noResumeMessage').style.display = 'none';

            // Display job recommendations
            const jobList = document.getElementById('jobList');
            jobList.innerHTML = '';

            if (data.job_recommendations && data.job_recommendations.length > 0) {
                data.job_recommendations.forEach(job => {
                    const jobCard = document.createElement('div');
                    jobCard.className = 'bg-white rounded-lg shadow-md p-6 mb-4';

                    // Safely handle recommended courses
                    const coursesList = (job.recommended_courses || []).map(course => {
                        if (typeof course === 'object' && course.course_name && course.link) {
                            return `
                            <li class="mb-2">
                                <a href="${course.link}" target="_blank" class="text-blue-600 hover:text-blue-800 flex items-center">
                                    ${course.course_name}
                                    <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                    </svg>
                                </a>
                            </li>
                        `;
                        }
                        return `<li class="mb-2 text-gray-500">No course available</li>`;
                    }).join('');

                    jobCard.innerHTML = `
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <h3 class="text-xl font-bold text-gray-900">${job.title || 'Position Available'}</h3>
                            <p class="text-gray-600">${job.company || 'Company Not Listed'}</p>
                        </div>
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${job.score >= 0.7 ? 'bg-green-100 text-green-800' :
                            job.score >= 0.4 ? 'bg-yellow-100 text-yellow-800' :
                                'bg-red-100 text-red-800'
                        }">
                            ${((job.score || 0) * 100).toFixed(0)}% Match
                        </span>
                    </div>

                    <div class="mb-4">
                        <p class="text-gray-700">${job.description ? job.description.substring(0, 200) + '...' : 'No description available'}</p>
                        ${job.link && job.link !== '#' ? `
                            <a href="${job.link}" target="_blank" class="text-blue-600 hover:text-blue-800 inline-flex items-center mt-2">
                                View Full Job Posting
                                <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                </svg>
                            </a>
                        ` : ''}
                    </div>

                    ${job.missing_skills && job.missing_skills.length > 0 ? `
                        <div class="mb-4">
                            <h4 class="font-semibold text-gray-900 mb-2">Missing Skills</h4>
                            <div class="flex flex-wrap gap-2">
                                ${job.missing_skills.map(skill => `
                                    <span class="inline-block bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-medium">
                                        ${skill}
                                    </span>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    ${coursesList ? `
                        <div>
                            <h4 class="font-semibold text-gray-900 mb-2">Recommended Courses</h4>
                            <ul class="list-none space-y-2">
                                ${coursesList}
                            </ul>
                        </div>
                    ` : ''}
                `;

                    jobList.appendChild(jobCard);
                });
            } else {
                jobList.innerHTML = '<p class="text-gray-500">No job recommendations found</p>';
            }

            // Phase 2: Draw the Career Roadmap Graph
            // If there are job recommendations, map the graph to the top recommendation
            if (data.job_recommendations && data.job_recommendations.length > 0) {
                if (window.fetchAndDrawGraph) {
                    window.fetchAndDrawGraph(data.job_recommendations[0].title);
                }
            } else {
                if (window.fetchAndDrawGraph) {
                    window.fetchAndDrawGraph();
                }
            }

            const optimizationTipsList = document.getElementById('optimizationTipsList');
            optimizationTipsList.innerHTML = '';

            if (data.optimization_tips && data.optimization_tips.length > 0) {
                data.optimization_tips.forEach(tip => {
                    // Clean the tip by trimming extra spaces, removing unwanted new lines, and removing stars for bold formatting
                    const cleanedTip = tip.trim().replace(/\s{2,}/g, ' ')  // Remove extra spaces
                        .replace(/\n/g, ' ')   // Remove new lines
                        .replace(/\*/g, '');   // Remove all stars (bold markers)

                    // Ensure the cleaned tip is not empty
                    if (cleanedTip) {
                        const tipItem = document.createElement('li');
                        tipItem.className = 'text-gray-800 mb-2 p-2 bg-gray-50 rounded shadow-sm';  // Added Tailwind styling
                        tipItem.textContent = cleanedTip;
                        optimizationTipsList.appendChild(tipItem);
                    }
                });
            } else {
                optimizationTipsList.innerHTML = '<li class="text-gray-500">No optimization tips available</li>';
            }

        })
        .catch(error => {
            console.error('Error:', error);
            progressBar.style.display = 'none';
            resultSection.style.display = 'block';
            resultSection.innerHTML = `
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                <strong>Error:</strong> Failed to process resume. Please try again.
            </div>
        `;
        });
});
