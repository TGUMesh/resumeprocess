document.getElementById('resumeForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const progressBar = document.getElementById('uploadProgress');
    const resultSection = document.getElementById('results');

    // Show loading state
    progressBar.classList.remove('hidden');
    // Ensure results remain hidden during processing
    resultSection.classList.add('hidden');
    resultSection.classList.remove('flex');

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
            progressBar.classList.add('hidden');

            // Show results panel
            resultSection.classList.remove('hidden');
            resultSection.classList.add('flex');

            // Display extracted skills
            const skillsList = document.getElementById('skillsList');
            skillsList.innerHTML = '';

            if (data.skills && data.skills.length > 0) {
                data.skills.forEach(skill => {
                    if (skill && skill.trim()) {
                        const badge = document.createElement('span');
                        badge.className = 'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm font-semibold bg-blue-50 text-blue-700 border border-blue-100 shadow-sm';
                        badge.innerHTML = `<svg class="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>${skill.trim()}`;
                        skillsList.appendChild(badge);
                    }
                });
            } else {
                skillsList.innerHTML = '<p class="text-gray-500">No skills extracted</p>';
            }

            const resumePreview = document.getElementById('resumePreview');
            resumePreview.classList.remove('hidden');

            const resumeIframe = document.getElementById('resumeIframe');
            resumeIframe.src = URL.createObjectURL(formData.get('resume'));
            resumeIframe.classList.remove('hidden');
            document.getElementById('noResumeMessage').classList.add('hidden');

            // Display job recommendations
            const jobList = document.getElementById('jobList');
            jobList.innerHTML = '';

            if (data.job_recommendations && data.job_recommendations.length > 0) {
                data.job_recommendations.forEach(job => {
                    const jobCard = document.createElement('div');
                    jobCard.className = 'bg-white border border-gray-100 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group';

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
                        <span class="inline-flex items-center px-3 py-1 rounded-xl text-sm font-bold shadow-sm ${job.score >= 0.7 ? 'bg-green-50 text-green-700 border border-green-200' :
                            job.score >= 0.4 ? 'bg-yellow-50 text-yellow-700 border border-yellow-200' :
                                'bg-red-50 text-red-700 border border-red-200'
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
                                    <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-red-50 text-red-700 border border-red-100">
                                        <svg class="w-3 h-3 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
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
                        tipItem.className = 'flex items-start gap-3 bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/10 shadow-sm';
                        tipItem.innerHTML = `<svg class="w-6 h-6 text-yellow-300 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                             <span class="leading-relaxed">${cleanedTip}</span>`;
                        optimizationTipsList.appendChild(tipItem);
                    }
                });
            } else {
                optimizationTipsList.innerHTML = '<li class="text-gray-500">No optimization tips available</li>';
            }

        })
        .catch(error => {
            console.error('Error:', error);
            progressBar.classList.add('hidden');
            resultSection.classList.remove('hidden');
            resultSection.classList.add('flex');
            resultSection.innerHTML = `
            <div class="w-full bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-2xl shadow-sm flex items-center gap-3">
                <svg class="w-6 h-6 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                <strong>Error:</strong> Failed to process resume or AI Rate Limit was reached. Please try again in 10 seconds.
            </div>
        `;
        });
});
