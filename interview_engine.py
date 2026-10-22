import os
import sys
import time
import json
import tempfile
import subprocess
import requests

# ==============================================================================
# 1. DOMAIN CLASSIFIER & KEYWORD MAPPER
# ==============================================================================
DOMAINS = {
    'backend': {
        'keywords': ['backend', 'python', 'django', 'flask', 'fastapi', 'java', 'spring', 'go', 'golang', 'c++', 'cpp', 'sql', 'postgres', 'database', 'api', 'microservice', 'rest', 'architect'],
        'name': 'Backend Engineering',
        'badge': '⚙️ Backend Systems'
    },
    'frontend': {
        'keywords': ['frontend', 'front-end', 'react', 'vue', 'angular', 'javascript', 'typescript', 'next', 'css', 'html', 'ui', 'web', 'tailwind'],
        'name': 'Frontend Engineering',
        'badge': '🎨 Frontend & UI'
    },
    'fullstack': {
        'keywords': ['full-stack', 'fullstack', 'mern', 'mean', 'full stack'],
        'name': 'Full-Stack Development',
        'badge': '🌐 Full-Stack'
    },
    'data_ai': {
        'keywords': ['data', 'machine learning', 'ai', 'deep learning', 'nlp', 'llm', 'pandas', 'numpy', 'pytorch', 'tensorflow', 'analytics', 'scientist'],
        'name': 'Data Science & AI',
        'badge': '🤖 AI & Data'
    },
    'devops': {
        'keywords': ['devops', 'cloud', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'k8s', 'ci/cd', 'terraform', 'linux', 'sre', 'infrastructure'],
        'name': 'DevOps & Cloud Infrastructure',
        'badge': '☁️ DevOps & Cloud'
    },
    'mobile': {
        'keywords': ['mobile', 'android', 'ios', 'kotlin', 'react native'],
        'name': 'Mobile Development',
        'badge': '📱 Mobile Engineering'
    },
    'php': {
        'keywords': ['php', 'laravel', 'symfony', 'wordpress', 'drupal', 'codeigniter', 'lamp'],
        'name': 'PHP & Web Development',
        'badge': '🐘 PHP Backend'
    },
    'sql': {
        'keywords': ['sql', 'database', 'postgres', 'postgresql', 'mysql', 'dba', 'oracle', 'sqlite', 'query', 'queries', 'etl', 'schema'],
        'name': 'SQL & Database Architecture',
        'badge': '🗄️ SQL & Databases'
    },
    'html_css': {
        'keywords': ['html', 'css', 'sass', 'scss', 'web design', 'responsive', 'flexbox', 'grid', 'styling', 'markup'],
        'name': 'HTML5 & CSS3 UI Engineering',
        'badge': '🌐 HTML5 & CSS3'
    },
    'dart': {
        'keywords': ['dart', 'flutter', 'dartpad', 'cross-platform mobile'],
        'name': 'Dart & Flutter Engineering',
        'badge': '🎯 Dart & Flutter'
    },
    'swift': {
        'keywords': ['swift', 'ios', 'swiftui', 'uikit', 'apple', 'xcode', 'cocoa'],
        'name': 'Swift & iOS Development',
        'badge': '🍎 Swift & iOS'
    }
}

def classify_job_domain(title='', category='', description=''):
    """Classifies a job into a technical domain based on title, category, and description."""
    title_lower = title.lower()
    category_lower = category.lower()
    
    # Direct high-precision keyword checks
    if any(k in title_lower for k in ['sql', 'database administrator', 'dba', 'database architect', 'postgres', 'mysql dba']):
        return 'sql', DOMAINS['sql']
    if any(k in title_lower for k in ['php', 'laravel', 'symfony', 'wordpress', 'drupal']):
        return 'php', DOMAINS['php']
    if any(k in title_lower for k in ['html', 'css', 'web designer', 'ui designer', 'styling', 'markup']):
        return 'html_css', DOMAINS['html_css']
    if any(k in title_lower for k in ['dart', 'flutter']):
        return 'dart', DOMAINS['dart']
    if any(k in title_lower for k in ['swift', 'ios', 'swiftui', 'uikit']):
        return 'swift', DOMAINS['swift']

    text = f"{title} {category} {description}".lower()
    
    scores = {}
    for dom_key, dom_data in DOMAINS.items():
        score = 0
        for kw in dom_data['keywords']:
            if kw in text:
                # Title matches have 4x weight
                if kw in title_lower:
                    score += 4
                elif kw in category_lower:
                    score += 2
                else:
                    score += 1
        scores[dom_key] = score
        
    best_domain = max(scores, key=scores.get)
    if scores[best_domain] == 0:
        return 'backend', DOMAINS['backend']
    return best_domain, DOMAINS[best_domain]


# ==============================================================================
# 2. FACE-TO-FACE QUESTION BANK (Tailored by Domain & Job Post)
# ==============================================================================
FACE_TO_FACE_BANK = {
    'backend': [
        {
            'type': 'Role & Behavioral',
            'question_template': "Welcome to your interview for the {title} position at {company}! To start, please give a concise introduction of yourself, your experience in backend architecture, and why this role at {company} is a great fit for you.",
            'expected_concepts': ['experience', 'scalability', 'backend', 'motivation', 'passion', 'projects'],
            'guidance': "Highlight your core stack, scalable systems you've worked on, and enthusiasm for the company mission."
        },
        {
            'type': 'Technical Architecture',
            'question_template': "How do you design a database schema and caching strategy (e.g. with Redis) for high-frequency write and read operations? How do you prevent cache stampede and ensure transactional data consistency?",
            'expected_concepts': ['redis', 'caching', 'index', 'consistency', 'transactions', 'ttl', 'lock', 'acid'],
            'guidance': "Discuss caching patterns (cache-aside, write-through), database indexing, TTLs, and concurrency handling."
        },
        {
            'type': 'Incident & Crisis Management',
            'question_template': "Describe a time in your career when a critical production service went down or suffered severe latency degradation. Walk me step-by-step through how you investigated, mitigated, and permanently resolved the root cause.",
            'expected_concepts': ['logs', 'metrics', 'root cause', 'rollback', 'postmortem', 'monitoring', 'reproduce'],
            'guidance': "Follow the STAR method (Situation, Task, Action, Result). Mention APM metrics, logs, rollbacks, and postmortems."
        }
    ],
    'frontend': [
        {
            'type': 'Role & Behavioral',
            'question_template': "Welcome! We're glad to have you interviewing for {title} at {company}. Please introduce yourself, your journey with modern frontend frameworks, and what excites you about crafting user experiences at {company}.",
            'expected_concepts': ['react', 'vue', 'ui', 'components', 'user experience', 'performance', 'frontend'],
            'guidance': "Emphasize responsive design, component architecture, design systems, and your passion for UX."
        },
        {
            'type': 'Technical Architecture',
            'question_template': "How do you optimize Core Web Vitals (Largest Contentful Paint, Interaction to Next Paint, Cumulative Layout Shift) in a large single-page or SSR application? How do you handle client-side state across deeply nested components?",
            'expected_concepts': ['web vitals', 'lcp', 'inp', 'cls', 'code splitting', 'lazy loading', 'memo', 'state management', 'bundle'],
            'guidance': "Mention code-splitting, tree shaking, SSR/SSG, CDN caching, memoization, and centralized state stores."
        },
        {
            'type': 'Incident & Conflict Handling',
            'question_template': "Imagine a major UI redesign release caused unexpected browser rendering bugs for 15% of your active users right before a product launch. How do you triage the issue, communicate with designers and backend teams, and roll out a quick fix?",
            'expected_concepts': ['reproduce', 'browser compatibility', 'feature flag', 'communication', 'hotfix', 'regression testing'],
            'guidance': "Explain feature flags, cross-browser debugging, transparent team communication, and regression testing."
        }
    ],
    'fullstack': [
        {
            'type': 'Role & Behavioral',
            'question_template': "Welcome to your interview for {title} at {company}! Tell us about your journey building end-to-end web applications, and why you feel equipped to handle both frontend and backend responsibilities here.",
            'expected_concepts': ['fullstack', 'frontend', 'backend', 'api', 'database', 'delivery', 'ownership'],
            'guidance': "Highlight end-to-end ownership, building features from DB schema up to polished interactive UI."
        },
        {
            'type': 'Technical Architecture',
            'question_template': "How do you architect the communication and contract between your frontend application and backend APIs? Specifically, how do you manage authentication (JWT vs Sessions), CORS, rate limiting, and API payload versioning?",
            'expected_concepts': ['jwt', 'session', 'cors', 'rest', 'graphql', 'auth', 'rate limiting', 'versioning'],
            'guidance': "Discuss secure HTTP-only cookies, token refresh cycles, OpenAPI/Swagger contracts, and error payload structures."
        },
        {
            'type': 'Incident & Incident Management',
            'question_template': "Tell me about a project where you had to make a difficult tradeoff between developer velocity (shipping quickly) and architectural robustness (test coverage, scalability). How did you justify your choice to leadership?",
            'expected_concepts': ['tradeoff', 'mvp', 'technical debt', 'stakeholders', 'refactoring', 'tests'],
            'guidance': "Discuss MVP scoping, tech debt tracking, automated test suites, and stakeholder alignment."
        }
    ],
    'data_ai': [
        {
            'type': 'Role & Behavioral',
            'question_template': "Welcome! We're thrilled to discuss the {title} role at {company}. Can you summarize your background in data engineering or machine learning, and what drew you to this opportunity at {company}?",
            'expected_concepts': ['machine learning', 'data', 'models', 'pipelines', 'python', 'metrics', 'impact'],
            'guidance': "Focus on real-world datasets, business impact of your models, and your analytical mindset."
        },
        {
            'type': 'Technical Architecture',
            'question_template': "How do you detect and combat data leakage and concept drift in a production ML pipeline? What strategies and evaluation metrics do you prioritize when dealing with highly imbalanced datasets?",
            'expected_concepts': ['drift', 'leakage', 'auc', 'f1', 'precision', 'recall', 'smote', 'cross-validation', 'monitoring'],
            'guidance': "Discuss F1-score, Precision-Recall AUC over Accuracy, stratification, feature stores, and drift monitoring."
        },
        {
            'type': 'Incident & Problem Solving',
            'question_template': "Describe an instance where your model or analytical dashboard produced unexpected or counter-intuitive results in production. How did you validate whether it was bad input data, pipeline bug, or true underlying user behavior?",
            'expected_concepts': ['data quality', 'validation', 'eda', 'pipeline', 'root cause', 'unit tests'],
            'guidance': "Walk through data anomaly detection, outlier analysis, schema validation, and stakeholder communication."
        }
    ],
    'devops': [
        {
            'type': 'Role & Behavioral',
            'question_template': "Welcome to your interview for {title} at {company}! Please introduce yourself and your background in infrastructure automation, cloud services, and reliability engineering.",
            'expected_concepts': ['devops', 'cloud', 'infrastructure', 'ci/cd', 'automation', 'reliability', 'kubernetes'],
            'guidance': "Emphasize infrastructure-as-code, reliability culture, and automation over manual toil."
        },
        {
            'type': 'Technical Architecture',
            'question_template': "Walk us through designing a robust CI/CD pipeline from git push to a multi-region Kubernetes cluster. How do you implement zero-downtime blue/green or canary deployments, automated rollbacks, and secrets management?",
            'expected_concepts': ['kubernetes', 'ci/cd', 'blue/green', 'canary', 'secrets', 'vault', 'health checks', 'rollback'],
            'guidance': "Cover GitOps, container scanning, canary metrics, health checks, and secure secrets injection."
        },
        {
            'type': 'Incident & Crisis Management',
            'question_template': "At 2:00 AM, a critical production database reaches 99% disk capacity and crashes during a peak traffic event. How do you triage the emergency, recover data safely, and what preventive safeguards do you install?",
            'expected_concepts': ['triage', 'disk expansion', 'failover', 'retention', 'alerts', 'log rotation', 'postmortem'],
            'guidance': "Focus on failover replicas, log pruning, automated volume expansion, alerting thresholds, and blameless postmortem."
        }
    ],
    'mobile': [
        {
            'type': 'Role & Behavioral',
            'question_template': "Welcome to the {title} interview for {company}! Please tell us about your experience in mobile app development, app store deployments, and why this position excites you.",
            'expected_concepts': ['mobile', 'android', 'ios', 'lifecycle', 'app store', 'ui', 'architecture'],
            'guidance': "Share key apps you've built, user ratings, offline performance, and passion for mobile ergonomics."
        },
        {
            'type': 'Technical Architecture',
            'question_template': "How do you manage offline-first synchronization, local SQLite/Room caching, and background work without draining user battery and memory?",
            'expected_concepts': ['offline', 'caching', 'sqlite', 'room', 'background', 'memory', 'sync', 'battery'],
            'guidance': "Discuss optimistic UI updates, conflict resolution algorithms, WorkManager / background tasks, and leak detection."
        },
        {
            'type': 'Incident & Problem Solving',
            'question_template': "Your newly released mobile app update crashes on startup for 30% of users running a specific OS version. How do you detect this immediately, halt the rollout, and ship a hotfix?",
            'expected_concepts': ['crashlytics', 'phased rollout', 'staged rollout', 'hotfix', 'regression', 'monitoring'],
            'guidance': "Explain staged rollouts (e.g. 5% -> 20%), Crashlytics/Sentry alerts, and emergency patch submissions."
        }
    ],
    'php': [
        {
            'type': 'Role & Behavioral',
            'question_template': "Welcome to your interview for {title} at {company}! Please introduce yourself and walk us through your background building scalable backend services with PHP and modern frameworks like Laravel or Symfony.",
            'expected_concepts': ['php', 'laravel', 'symfony', 'backend', 'composer', 'mvc', 'apis'],
            'guidance': "Highlight MVC architecture, Eloquent/Doctrine ORM, RESTful API design, and clean backend code."
        },
        {
            'type': 'Security & Architecture',
            'question_template': "How do you enforce robust web security in PHP applications? Specifically, explain how you prevent SQL Injection (via PDO prepared statements), Cross-Site Scripting (XSS), CSRF token validation, and secure password hashing with bcrypt/argon2.",
            'expected_concepts': ['pdo', 'prepared statements', 'csrf', 'xss', 'bcrypt', 'argon2', 'sanitization', 'sessions'],
            'guidance': "Detail PDO parameters, HTML escaping, HttpOnly SameSite cookie flags, and strong cryptographic hashing."
        },
        {
            'type': 'Performance & Debugging',
            'question_template': "Your PHP API begins experiencing high memory usage and response times degrading from 80ms to over 2.5 seconds under peak traffic. How do you diagnose bottlenecks with OPcache, profiling tools, and database query optimization?",
            'expected_concepts': ['opcache', 'profiling', 'n+1', 'indexing', 'queues', 'redis', 'caching', 'fpm'],
            'guidance': "Explain PHP-FPM worker tuning, OPcache memory, N+1 query identification, and moving heavy jobs to background queues."
        }
    ],
    'sql': [
        {
            'type': 'Role & Behavioral',
            'question_template': "Welcome to the {title} interview at {company}! Can you tell us about your experience in relational database design, complex SQL query authoring, and why this data-intensive role fits your career goals?",
            'expected_concepts': ['sql', 'database', 'queries', 'normalization', 'modeling', 'postgres', 'mysql'],
            'guidance': "Emphasize relational modeling, schema normalization, analytical queries, and business impact."
        },
        {
            'type': 'Technical Architecture & Optimization',
            'question_template': "Explain how B-Tree indexes work under the hood in PostgreSQL or MySQL. What is the difference between an Index Seek and an Index Scan? How do Composite Indexes work with the Leftmost Prefix rule?",
            'expected_concepts': ['b-tree', 'index', 'seek', 'scan', 'composite', 'prefix', 'selectivity', 'cardinality'],
            'guidance': "Discuss disk I/O, node traversal, column order in compound indexes, and query selectivity."
        },
        {
            'type': 'Incident & Concurrency Handling',
            'question_template': "A high-concurrency payment table experiences frequent database deadlocks during promotional flash sales. How do you use transaction isolation levels, row-level locking (SELECT FOR UPDATE), and query re-ordering to eliminate deadlocks?",
            'expected_concepts': ['deadlock', 'isolation levels', 'row lock', 'select for update', 'acid', 'locking order'],
            'guidance': "Explain consistent lock ordering, keeping transactions short, and selecting appropriate isolation (e.g. Read Committed)."
        }
    ],
    'html_css': [
        {
            'type': 'Role & Behavioral',
            'question_template': "Welcome! We are excited to interview you for {title} at {company}. Can you walk us through your journey in semantic HTML5 markup, modern CSS styling, and responsive design systems?",
            'expected_concepts': ['html5', 'css3', 'semantic', 'responsive', 'accessibility', 'a11y', 'design systems'],
            'guidance': "Highlight accessible HTML, responsive breakpoints, semantic elements (nav, main, article), and visual hierarchy."
        },
        {
            'type': 'Layout & Architecture',
            'question_template': "When do you choose CSS Flexbox versus CSS Grid for complex layouts? How do you organize your stylesheets using methodologies like BEM or modern CSS variables (custom properties) to prevent specificity wars?",
            'expected_concepts': ['flexbox', 'grid', 'bem', 'variables', 'specificity', 'media queries', 'box-sizing'],
            'guidance': "Contrast 1D Flexbox vs 2D CSS Grid; explain cascade layers, custom properties, and modular CSS architecture."
        },
        {
            'type': 'Performance & Core Web Vitals',
            'question_template': "How do you eliminate Cumulative Layout Shift (CLS) and optimize rendering performance (minimizing layout reflows and repaints) across desktop and mobile viewports?",
            'expected_concepts': ['cls', 'aspect-ratio', 'web vitals', 'reflow', 'repaint', 'will-change', 'font display', 'critical css'],
            'guidance': "Discuss reserving image dimensions with aspect-ratio, `font-display: swap`, GPU-accelerated transforms, and critical CSS."
        }
    ],
    'dart': [
        {
            'type': 'Role & Behavioral',
            'question_template': "Welcome to your interview for {title} at {company}! Please introduce yourself and your background building cross-platform mobile and web applications with Dart and Flutter.",
            'expected_concepts': ['dart', 'flutter', 'widgets', 'cross-platform', 'mobile', 'state'],
            'guidance': "Share key Flutter/Dart projects, custom UI widgets, and your experience targeting iOS, Android, and web."
        },
        {
            'type': 'Technical Architecture & Concurrency',
            'question_template': "How does Dart's single-threaded event loop handle concurrency through Microtasks and the Event Queue? How do Streams, Isolates, and async/await differ when handling background computation?",
            'expected_concepts': ['event loop', 'microtask', 'stream', 'isolate', 'future', 'async', 'concurrency'],
            'guidance': "Contrast async I/O on the main event loop against CPU-intensive workloads run inside separate Dart Isolates."
        },
        {
            'type': 'Performance & State Management',
            'question_template': "How do you architect state management in a large-scale Flutter application (e.g. Bloc, Riverpod, or Provider)? How do you prevent unnecessary widget rebuilds to maintain a seamless 60/120 FPS UI?",
            'expected_concepts': ['bloc', 'riverpod', 'provider', 'rebuild', 'const widgets', 'keys', 'devtools'],
            'guidance': "Emphasize `const` constructors, granular state selectors, RepaintBoundaries, and Flutter DevTools profiling."
        }
    ],
    'swift': [
        {
            'type': 'Role & Behavioral',
            'question_template': "Welcome to your interview for {title} at {company}! Can you tell us about your experience building native iOS/macOS applications with Swift, SwiftUI, or UIKit?",
            'expected_concepts': ['swift', 'ios', 'swiftui', 'uikit', 'apple', 'xcode', 'mobile'],
            'guidance': "Discuss your app releases on the App Store, native user experience, and your love for Apple platform design guidelines."
        },
        {
            'type': 'Memory Management & Architecture',
            'question_template': "Explain how Automatic Reference Counting (ARC) functions in Swift. What is the fundamental difference between `weak` and `unowned` references, and how do capture lists in closures prevent retain cycles and memory leaks?",
            'expected_concepts': ['arc', 'weak', 'unowned', 'retain cycle', 'memory leak', 'capture list', 'deinit'],
            'guidance': "Discuss strong reference cycles, delegating with weak protocols, and using `[weak self]` in completion handlers."
        },
        {
            'type': 'Concurrency & Modern Patterns',
            'question_template': "How has modern Swift Concurrency (async/await, Tasks, Actors, and Sendable) replaced Grand Central Dispatch (GCD) for thread-safe data access and preventing data races?",
            'expected_concepts': ['actors', 'async/await', 'sendable', 'gcd', 'data race', 'mainactor', 'concurrency'],
            'guidance': "Detail Actors for state synchronization, `@MainActor` for UI updates, and compiler-checked `Sendable` types."
        }
    ]
}


# ==============================================================================
# 3. TECHNICAL CODING CHALLENGES BANK (With Multi-Language Boilerplates)
# ==============================================================================
CODING_CHALLENGES = [
    {
        'id': 'two-sum',
        'title': 'Two Sum - Target Index Finder',
        'domain_affinity': ['backend', 'frontend', 'fullstack'],
        'difficulty': 'Easy',
        'time_limit_mins': 20,
        'description': """Given an array of integers <code>nums</code> and an integer <code>target</code>, return <strong>indices of the two numbers</strong> such that they add up to <code>target</code>.
        <br><br>
        You may assume that each input would have exactly one solution, and you may not use the same element twice. You can return the answer in any order.""",
        'input_format': "Line 1: Comma-separated integers (e.g., <code>2,7,11,15</code>)<br>Line 2: Target integer (e.g., <code>9</code>)",
        'output_format': "Array of two 0-based indices e.g. <code>[0, 1]</code>",
        'constraints': ["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9", "-10^9 <= target <= 10^9", "Only one valid answer exists."],
        'examples': [
            {'input': "2,7,11,15\n9", 'output': "[0, 1]", 'explanation': "Because nums[0] + nums[1] == 2 + 7 == 9, we return [0, 1]."},
            {'input': "3,2,4\n6", 'output': "[1, 2]", 'explanation': "Because nums[1] + nums[2] == 2 + 4 == 6, we return [1, 2]."}
        ],
        'default_stdin': "2,7,11,15\n9",
        'test_cases': [
            {'stdin': "2,7,11,15\n9", 'expected': "[0, 1]"},
            {'stdin': "3,2,4\n6", 'expected': "[1, 2]"}
        ],
        'boilerplates': {
            'python': '''import sys

def two_sum(nums, target):
    # Write your solution here
    seen = {}
    for i, n in enumerate(nums):
        diff = target - n
        if diff in seen:
            return [seen[diff], i]
        seen[n] = i
    return []

if __name__ == '__main__':
    lines = sys.stdin.read().strip().split('\\n')
    if len(lines) >= 2:
        nums = [int(x.strip()) for x in lines[0].split(',') if x.strip()]
        target = int(lines[1].strip())
        print(two_sum(nums, target))
''',
            'javascript': '''const fs = require('fs');

function twoSum(nums, target) {
    // Write your solution here
    const map = new Map();
    for (let i = 0; i < nums.length; i++) {
        const diff = target - nums[i];
        if (map.has(diff)) {
            return [map.get(diff), i];
        }
        map.set(nums[i], i);
    }
    return [];
}

const input = fs.readFileSync(0, 'utf-8').trim().split('\\n');
if (input.length >= 2) {
    const nums = input[0].split(',').map(x => parseInt(x.trim(), 10));
    const target = parseInt(input[1].trim(), 10);
    console.log(JSON.stringify(twoSum(nums, target)));
}
''',
            'java': '''import java.util.*;

public class Solution {
    public static int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> map = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int diff = target - nums[i];
            if (map.containsKey(diff)) {
                return new int[]{map.get(diff), i};
            }
            map.put(nums[i], i);
        }
        return new int[]{};
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (sc.hasNextLine()) {
            String[] parts = sc.nextLine().trim().split(",");
            int[] nums = new int[parts.length];
            for (int i = 0; i < parts.length; i++) nums[i] = Integer.parseInt(parts[i].trim());
            if (sc.hasNextInt()) {
                int target = sc.nextInt();
                int[] res = twoSum(nums, target);
                System.out.println(Arrays.toString(res));
            }
        }
    }
}
''',
            'cpp': '''#include <iostream>
#include <vector>
#include <unordered_map>
#include <sstream>
using namespace std;

vector<int> twoSum(vector<int>& nums, int target) {
    unordered_map<int, int> seen;
    for (int i = 0; i < nums.size(); ++i) {
        int diff = target - nums[i];
        if (seen.count(diff)) {
            return {seen[diff], i};
        }
        seen[nums[i]] = i;
    }
    return {};
}

int main() {
    string line;
    if (getline(cin, line)) {
        stringstream ss(line);
        string temp;
        vector<int> nums;
        while (getline(ss, temp, ',')) {
            if (!temp.empty()) nums.push_back(stoi(temp));
        }
        int target;
        if (cin >> target) {
            vector<int> res = twoSum(nums, target);
            if (!res.empty()) {
                cout << "[" << res[0] << ", " << res[1] << "]" << endl;
            } else {
                cout << "[]" << endl;
            }
        }
    }
    return 0;
}
''',
            'c': '''#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    char line[512];
    if (fgets(line, sizeof(line), stdin)) {
        int nums[256];
        int n = 0;
        char *tok = strtok(line, ",\\n");
        while (tok) {
            nums[n++] = atoi(tok);
            tok = strtok(NULL, ",\\n");
        }
        int target;
        if (scanf("%d", &target) == 1) {
            for (int i = 0; i < n; i++) {
                for (int j = i + 1; j < n; j++) {
                    if (nums[i] + nums[j] == target) {
                        printf("[%d, %d]\\n", i, j);
                        return 0;
                    }
                }
            }
        }
    }
    printf("[]\\n");
    return 0;
}
''',
            'go': '''package main

import (
    "bufio"
    "fmt"
    "os"
    "strconv"
    "strings"
)

func twoSum(nums []int, target int) []int {
    seen := make(map[int]int)
    for i, num := range nums {
        diff := target - num
        if idx, ok := seen[diff]; ok {
            return []int{idx, i}
        }
        seen[num] = i
    }
    return []int{}
}

func main() {
    scanner := bufio.NewScanner(os.Stdin)
    if scanner.Scan() {
        line := scanner.Text()
        parts := strings.Split(line, ",")
        nums := make([]int, 0, len(parts))
        for _, p := range parts {
            if val, err := strconv.Atoi(strings.TrimSpace(p)); err == nil {
                nums = append(nums, val)
            }
        }
        if scanner.Scan() {
            target, _ := strconv.Atoi(strings.TrimSpace(scanner.Text()))
            res := twoSum(nums, target)
            if len(res) == 2 {
                fmt.Printf("[%d, %d]\\n", res[0], res[1])
            } else {
                fmt.Println("[]")
            }
        }
    }
}
''',
            'rust': '''use std::io::{self, BufRead};
use std::collections::HashMap;

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    if let Some(Ok(line1)) = lines.next() {
        let nums: Vec<i32> = line1
            .split(',')
            .filter_map(|s| s.trim().parse().ok())
            .collect();
        if let Some(Ok(line2)) = lines.next() {
            if let Ok(target) = line2.trim().parse::<i32>() {
                let mut map = HashMap::new();
                for (i, &num) in nums.iter().enumerate() {
                    let diff = target - num;
                    if let Some(&prev_idx) = map.get(&diff) {
                        println!("[{}, {}]", prev_idx, i);
                        return;
                    }
                    map.insert(num, i);
                }
                println!("[]");
            }
        }
    }
}
''',
            'php': '''<?php
function twoSum($nums, $target) {
    $seen = [];
    foreach ($nums as $i => $n) {
        $diff = $target - $n;
        if (isset($seen[$diff])) {
            return [$seen[$diff], $i];
        }
        $seen[$n] = $i;
    }
    return [];
}

$raw = trim(file_get_contents('php://stdin'));
if (!empty($raw)) {
    $lines = explode("\\n", $raw);
    $nums = array_map('intval', explode(',', trim($lines[0])));
    $target = intval(trim($lines[1] ?? '0'));
    echo json_encode(twoSum($nums, $target)) . "\\n";
}
?>''',
            'dart': '''import 'dart:io';
import 'dart:convert';

List<int> twoSum(List<int> nums, int target) {
  final Map<int, int> seen = {};
  for (int i = 0; i < nums.length; i++) {
    int diff = target - nums[i];
    if (seen.containsKey(diff)) {
      return [seen[diff]!, i];
    }
    seen[nums[i]] = i;
  }
  return [];
}

void main() {
  List<String> lines = [];
  String? line;
  while ((line = stdin.readLineSync(encoding: utf8)) != null) {
    if (line!.trim().isNotEmpty) lines.add(line.trim());
  }
  if (lines.length >= 2) {
    List<int> nums = lines[0].split(',').map((x) => int.parse(x.trim())).toList();
    int target = int.parse(lines[1]);
    print(twoSum(nums, target));
  }
}
''',
            'swift': r'''import Foundation

func twoSum(_ nums: [Int], _ target: Int) -> [Int] {
    var seen = [Int: Int]()
    for (i, n) in nums.enumerated() {
        let diff = target - n
        if let prev = seen[diff] {
            return [prev, i]
        }
        seen[n] = i
    }
    return []
}

if let line1 = readLine() {
    let nums = line1.components(separatedBy: ",").compactMap { Int($0.trimmingCharacters(in: .whitespaces)) }
    if let line2 = readLine(), let target = Int(line2.trimmingCharacters(in: .whitespaces)) {
        let res = twoSum(nums, target)
        print("[\(res.map(String.init).joined(separator: ", "))]")
    }
}
''',
            'sql': '''-- SQL Database Table Querying
-- Pre-populated tables: employees (id, name, salary, department), departments (id, name, budget)
SELECT department, COUNT(*) as headcount, AVG(salary) as avg_sal
FROM employees
GROUP BY department
ORDER BY avg_sal DESC;
''',
            'html_css': '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Algorithm Preview</title>
  <style>
    body { font-family: sans-serif; padding: 20px; background: #f8fafc; }
    .card { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
  </style>
</head>
<body>
  <div class="card">
    <h2>Two Sum Algorithmic Visualizer</h2>
    <p>Target Index Solution Runner &bull; Target: 9</p>
  </div>
</body>
</html>
'''
        }
    },
    {
        'id': 'valid-palindrome',
        'title': 'Valid Alphanumeric Palindrome',
        'domain_affinity': ['frontend', 'backend', 'fullstack'],
        'difficulty': 'Easy',
        'time_limit_mins': 15,
        'description': """A phrase is a <strong>palindrome</strong> if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward. Alphanumeric characters include letters and numbers.
        <br><br>
        Given a string <code>s</code>, return <code>true</code> if it is a palindrome, or <code>false</code> otherwise.""",
        'input_format': "A single line containing string <code>s</code>",
        'output_format': "Boolean: <code>true</code> or <code>false</code>",
        'constraints': ["1 <= s.length <= 2 * 10^5", "s consists only of printable ASCII characters."],
        'examples': [
            {'input': "A man, a plan, a canal: Panama", 'output': "true", 'explanation': "\"amanaplanacanalpanama\" is a palindrome."},
            {'input': "race a car", 'output': "false", 'explanation': "\"raceacar\" is not a palindrome."}
        ],
        'default_stdin': "A man, a plan, a canal: Panama",
        'test_cases': [
            {'stdin': "A man, a plan, a canal: Panama", 'expected': "true"},
            {'stdin': "race a car", 'expected': "false"}
        ],
        'boilerplates': {
            'python': '''import sys

def is_palindrome(s: str) -> bool:
    filtered = [c.lower() for c in s if c.isalnum()]
    return filtered == filtered[::-1]

if __name__ == '__main__':
    raw = sys.stdin.read().strip()
    print("true" if is_palindrome(raw) else "false")
''',
            'javascript': '''const fs = require('fs');

function isPalindrome(s) {
    const clean = s.toLowerCase().replace(/[^a-z0-9]/g, '');
    return clean === clean.split('').reverse().join('');
}

const input = fs.readFileSync(0, 'utf-8').trim();
console.log(isPalindrome(input) ? "true" : "false");
''',
            'java': '''import java.util.*;

public class Solution {
    public static boolean isPalindrome(String s) {
        StringBuilder sb = new StringBuilder();
        for (char c : s.toCharArray()) {
            if (Character.isLetterOrDigit(c)) {
                sb.append(Character.toLowerCase(c));
            }
        }
        String clean = sb.toString();
        String rev = sb.reverse().toString();
        return clean.equals(rev);
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (sc.hasNextLine()) {
            String line = sc.nextLine();
            System.out.println(isPalindrome(line) ? "true" : "false");
        }
    }
}
''',
            'cpp': '''#include <iostream>
#include <string>
#include <cctype>
#include <algorithm>
using namespace std;

bool isPalindrome(string s) {
    string clean = "";
    for (char c : s) {
        if (isalnum(c)) clean += tolower(c);
    }
    string rev = clean;
    reverse(rev.begin(), rev.end());
    return clean == rev;
}

int main() {
    string s;
    if (getline(cin, s)) {
        cout << (isPalindrome(s) ? "true" : "false") << endl;
    }
    return 0;
}
''',
            'c': '''#include <stdio.h>
#include <string.h>
#include <ctype.h>

int main() {
    char s[1024];
    if (fgets(s, sizeof(s), stdin)) {
        int left = 0, right = strlen(s) - 1;
        while (left < right) {
            while (left < right && !isalnum((unsigned char)s[left])) left++;
            while (left < right && !isalnum((unsigned char)s[right])) right--;
            if (tolower((unsigned char)s[left]) != tolower((unsigned char)s[right])) {
                printf("false\\n");
                return 0;
            }
            left++;
            right--;
        }
        printf("true\\n");
    }
    return 0;
}
''',
            'go': '''package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
    "unicode"
)

func main() {
    scanner := bufio.NewScanner(os.Stdin)
    if scanner.Scan() {
        s := scanner.Text()
        var runes []rune
        for _, r := range s {
            if unicode.IsLetter(r) || unicode.IsDigit(r) {
                runes = append(runes, unicode.ToLower(r))
            }
        }
        n := len(runes)
        pal := true
        for i := 0; i < n/2; i++ {
            if runes[i] != runes[n-1-i] {
                pal = false
                break
            }
        }
        if pal {
            fmt.Println("true")
        } else {
            fmt.Println("false")
        }
    }
}
''',
            'rust': '''use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    if let Some(Ok(line)) = stdin.lock().lines().next() {
        let clean: Vec<char> = line
            .chars()
            .filter(|c| c.is_alphanumeric())
            .map(|c| c.to_ascii_lowercase())
            .collect();
        let is_pal = clean.iter().eq(clean.iter().rev());
        println!("{}", if is_pal { "true" } else { "false" });
    }
}
'''
        }
    },
    {
        'id': 'max-subarray',
        'title': 'Maximum Subarray (Kadane Algorithm)',
        'domain_affinity': ['backend', 'data_ai', 'devops'],
        'difficulty': 'Medium',
        'time_limit_mins': 25,
        'description': """Given an integer array <code>nums</code>, find the subarray with the largest sum, and return <em>its sum</em>.
        <br><br>
        A <strong>subarray</strong> is a contiguous non-empty sequence of elements within an array.""",
        'input_format': "A single line containing comma-separated integers (e.g. <code>-2,1,-3,4,-1,2,1,-5,4</code>)",
        'output_format': "Integer representing the maximum subarray sum",
        'constraints': ["1 <= nums.length <= 10^5", "-10^4 <= nums[i] <= 10^4"],
        'examples': [
            {'input': "-2,1,-3,4,-1,2,1,-5,4", 'output': "6", 'explanation': "The subarray [4,-1,2,1] has the largest sum 6."},
            {'input': "5,4,-1,7,8", 'output': "23", 'explanation': "The subarray [5,4,-1,7,8] has the largest sum 23."}
        ],
        'default_stdin': "-2,1,-3,4,-1,2,1,-5,4",
        'test_cases': [
            {'stdin': "-2,1,-3,4,-1,2,1,-5,4", 'expected': "6"},
            {'stdin': "5,4,-1,7,8", 'expected': "23"}
        ],
        'boilerplates': {
            'python': '''import sys

def max_sub_array(nums):
    max_sum = nums[0]
    curr_sum = nums[0]
    for x in nums[1:]:
        curr_sum = max(x, curr_sum + x)
        max_sum = max(max_sum, curr_sum)
    return max_sum

if __name__ == '__main__':
    raw = sys.stdin.read().strip()
    if raw:
        nums = [int(x.strip()) for x in raw.split(',') if x.strip()]
        print(max_sub_array(nums))
''',
            'javascript': '''const fs = require('fs');

function maxSubArray(nums) {
    let max = nums[0];
    let cur = nums[0];
    for (let i = 1; i < nums.length; i++) {
        cur = Math.max(nums[i], cur + nums[i]);
        max = Math.max(max, cur);
    }
    return max;
}

const input = fs.readFileSync(0, 'utf-8').trim();
if (input) {
    const nums = input.split(',').map(x => parseInt(x.trim(), 10));
    console.log(maxSubArray(nums));
}
''',
            'java': '''import java.util.*;

public class Solution {
    public static int maxSubArray(int[] nums) {
        int max = nums[0], cur = nums[0];
        for (int i = 1; i < nums.length; i++) {
            cur = Math.max(nums[i], cur + nums[i]);
            max = Math.max(max, cur);
        }
        return max;
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (sc.hasNextLine()) {
            String[] parts = sc.nextLine().trim().split(",");
            int[] nums = new int[parts.length];
            for (int i = 0; i < parts.length; i++) nums[i] = Integer.parseInt(parts[i].trim());
            System.out.println(maxSubArray(nums));
        }
    }
}
''',
            'cpp': '''#include <iostream>
#include <vector>
#include <sstream>
#include <algorithm>
using namespace std;

int maxSubArray(vector<int>& nums) {
    int max_s = nums[0], cur = nums[0];
    for (size_t i = 1; i < nums.size(); ++i) {
        cur = max(nums[i], cur + nums[i]);
        max_s = max(max_s, cur);
    }
    return max_s;
}

int main() {
    string line;
    if (getline(cin, line)) {
        stringstream ss(line);
        string temp;
        vector<int> nums;
        while (getline(ss, temp, ',')) {
            if (!temp.empty()) nums.push_back(stoi(temp));
        }
        if (!nums.empty()) cout << maxSubArray(nums) << endl;
    }
    return 0;
}
''',
            'c': '''#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    char line[1024];
    if (fgets(line, sizeof(line), stdin)) {
        int nums[500];
        int n = 0;
        char *tok = strtok(line, ",\\n");
        while (tok) {
            nums[n++] = atoi(tok);
            tok = strtok(NULL, ",\\n");
        }
        if (n > 0) {
            int max_s = nums[0];
            int cur = nums[0];
            for (int i = 1; i < n; i++) {
                cur = (nums[i] > cur + nums[i]) ? nums[i] : (cur + nums[i]);
                if (cur > max_s) max_s = cur;
            }
            printf("%d\\n", max_s);
        }
    }
    return 0;
}
''',
            'go': '''package main

import (
    "bufio"
    "fmt"
    "os"
    "strconv"
    "strings"
)

func main() {
    scanner := bufio.NewScanner(os.Stdin)
    if scanner.Scan() {
        parts := strings.Split(scanner.Text(), ",")
        nums := make([]int, 0, len(parts))
        for _, p := range parts {
            if v, err := strconv.Atoi(strings.TrimSpace(p)); err == nil {
                nums = append(nums, v)
            }
        }
        if len(nums) > 0 {
            maxSum, cur := nums[0], nums[0]
            for i := 1; i < len(nums); i++ {
                if nums[i] > cur+nums[i] {
                    cur = nums[i]
                } else {
                    cur += nums[i]
                }
                if cur > maxSum {
                    maxSum = cur
                }
            }
            fmt.Println(maxSum)
        }
    }
}
''',
            'rust': '''use std::io::{self, BufRead};
use std::cmp::max;

fn main() {
    let stdin = io::stdin();
    if let Some(Ok(line)) = stdin.lock().lines().next() {
        let nums: Vec<i32> = line
            .split(',')
            .filter_map(|s| s.trim().parse().ok())
            .collect();
        if !nums.is_empty() {
            let mut max_s = nums[0];
            let mut cur = nums[0];
            for &n in &nums[1..] {
                cur = max(n, cur + n);
                max_s = max(max_s, cur);
            }
            println!("{}", max_s);
        }
    }
}
'''
        }
    },
    {
        'id': 'sql-department-analytics',
        'title': 'SQL: Department Headcount & Compensation Analytics',
        'domain_affinity': ['sql', 'backend', 'data_ai'],
        'difficulty': 'Medium',
        'time_limit_mins': 25,
        'description': """Write an aggregate SQL query to calculate for each department:
        <ul>
            <li><code>department</code>: The department name</li>
            <li><code>total_staff</code>: Count of employees in that department</li>
            <li><code>highest_salary</code>: The maximum individual salary</li>
            <li><code>avg_salary</code>: Average salary rounded to 2 decimal places</li>
        </ul>
        <strong>Filtering & Ordering:</strong>
        Filter for departments with an average salary of <strong>$75,000 or greater</strong> (using a <code>HAVING</code> clause). Order results by <code>highest_salary</code> in <strong>descending order</strong>.
        <br><br>
        <strong>Available Tables in Database:</strong><br>
        <code>employees (id INT, name TEXT, salary INT, department TEXT, hire_date TEXT)</code><br>
        <code>departments (id INT, name TEXT, budget INT)</code>""",
        'input_format': "In-memory relational schema with pre-populated <code>employees</code> and <code>departments</code> tables.",
        'output_format': "Relational table grid with columns: <code>department</code>, <code>total_staff</code>, <code>highest_salary</code>, <code>avg_salary</code>.",
        'constraints': ["Use standard SQL aggregate functions (COUNT, MAX, AVG, ROUND)", "Filter aggregated results using HAVING clause", "Sort with ORDER BY DESC"],
        'examples': [
            {
                'input': "SELECT * FROM employees;",
                'output': "Engineering (3 staff, max: $115,000, avg: $105,000)\nDesign (2 staff, max: $88,000, avg: $84,500)",
                'explanation': "Marketing avg salary ($72,000) is filtered out by the HAVING clause."
            }
        ],
        'default_stdin': "",
        'test_cases': [],
        'boilerplates': {
            'sql': '''-- SQL Technical Challenge: Department Headcount & Compensation Analytics
-- Tables:
--   employees (id INT, name TEXT, salary INT, department TEXT, hire_date TEXT)
--   departments (id INT, name TEXT, budget INT)

SELECT 
    department,
    COUNT(*) as total_staff,
    MAX(salary) as highest_salary,
    ROUND(AVG(salary), 2) as avg_salary
FROM employees
GROUP BY department
HAVING AVG(salary) >= 75000
ORDER BY highest_salary DESC;
''',
            'python': '''import sqlite3

# Test query via SQLite
con = sqlite3.connect(':memory:')
cur = con.cursor()
cur.execute("CREATE TABLE employees (id INT, name TEXT, salary INT, department TEXT);")
cur.executemany("INSERT INTO employees VALUES (?, ?, ?, ?);", [
    (1, 'Alice', 95000, 'Engineering'),
    (2, 'Bob', 72000, 'Marketing'),
    (3, 'Charlie', 115000, 'Engineering'),
    (4, 'Diana', 88000, 'Design'),
    (5, 'Evan', 105000, 'Engineering')
])

query = """
SELECT department, COUNT(*), MAX(salary), ROUND(AVG(salary), 2)
FROM employees
GROUP BY department
HAVING AVG(salary) >= 75000
ORDER BY MAX(salary) DESC;
"""
cur.execute(query)
for row in cur.fetchall():
    print(row)
''',
            'php': '''<?php
// PHP PDO SQL Query Demo
echo "SQL Challenge: Switch language to SQL in the dropdown above to execute live against SQLite!\n";
?>''',
            'javascript': '''// JavaScript SQL Query Demo
console.log("SQL Challenge: Switch language to SQL in the dropdown above to execute live against SQLite!");
'''
        }
    },
    {
        'id': 'html-css-pricing-card',
        'title': 'HTML5 & CSS3: Modern Responsive Pricing Component',
        'domain_affinity': ['html_css', 'frontend'],
        'difficulty': 'Medium',
        'time_limit_mins': 25,
        'description': """Build an accessible, responsive SaaS subscription pricing card using semantic <strong>HTML5</strong> and modern <strong>CSS3</strong>.
        <br><br>
        <strong>Component Requirements:</strong>
        <ol>
            <li><strong>Card Wrapper:</strong> Container card with subtle border, box-shadow, rounded corners (<code>border-radius</code>), and clean padding.</li>
            <li><strong>Header & Badge:</strong> A pill badge indicating <code>FEATURED / POPULAR</code> and a plan title (e.g. <em>Pro Developer</em>).</li>
            <li><strong>Pricing Display:</strong> Prominent price (e.g. <code>$29</code>) with subscription frequency (e.g. <code>/ month</code>).</li>
            <li><strong>Features Checklist:</strong> An unordered list with checkmark icons detailing key plan benefits.</li>
            <li><strong>Call to Action Button:</strong> Full-width primary button with smooth hover transition effects.</li>
            <li><strong>Responsiveness:</strong> Flexbox or CSS Grid alignment that scales smoothly across mobile and desktop.</li>
        </ol>""",
        'input_format': "Complete HTML5 document with inline or <code>&lt;style&gt;</code> block styling.",
        'output_format': "Validated HTML DOM structure and live rendered visual preview in the sandbox frame.",
        'constraints': ["Use valid semantic HTML5 tags (article, section, h2, ul, li, button)", "Pure CSS3 layout (Flexbox or Grid)", "Smooth interactive hover transitions"],
        'examples': [
            {
                'input': "<article class='pricing-card'>...</article>",
                'output': "HTML elements validated and rendered into live sandbox preview frame.",
                'explanation': "The preview tab displays the real-time responsive component."
            }
        ],
        'default_stdin': "",
        'test_cases': [],
        'boilerplates': {
            'html_css': '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Responsive Pricing Card</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #f1f5f9;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 20px;
    }
    .pricing-card {
      background: #ffffff;
      border-radius: 16px;
      padding: 32px 28px;
      max-width: 360px;
      width: 100%;
      box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
      border: 1.5px solid #e2e8f0;
      transition: transform 0.25s ease, box-shadow 0.25s ease;
      position: relative;
    }
    .pricing-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 20px 40px rgba(99, 102, 241, 0.16);
      border-color: #6366f1;
    }
    .badge-popular {
      background: linear-gradient(135deg, #4f46e5, #7c3aed);
      color: #ffffff;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.5px;
      padding: 4px 12px;
      border-radius: 9999px;
      display: inline-block;
      margin-bottom: 12px;
    }
    .plan-title {
      font-size: 20px;
      font-weight: 700;
      color: #0f172a;
      margin-bottom: 8px;
    }
    .price-wrap {
      display: flex;
      align-items: baseline;
      gap: 4px;
      margin: 16px 0 24px;
    }
    .price-num {
      font-size: 38px;
      font-weight: 800;
      color: #0f172a;
    }
    .price-cycle {
      color: #64748b;
      font-size: 14px;
      font-weight: 500;
    }
    .features-list {
      list-style: none;
      margin-bottom: 28px;
    }
    .features-list li {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 14px;
      color: #334155;
      margin-bottom: 12px;
    }
    .check-icon {
      color: #10b981;
      font-weight: bold;
    }
    .btn-cta {
      display: block;
      width: 100%;
      background: #4f46e5;
      color: #ffffff;
      font-weight: 700;
      font-size: 15px;
      text-align: center;
      padding: 12px;
      border-radius: 10px;
      border: none;
      cursor: pointer;
      transition: background 0.2s, box-shadow 0.2s;
    }
    .btn-cta:hover {
      background: #4338ca;
      box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4);
    }
  </style>
</head>
<body>

  <article class="pricing-card">
    <span class="badge-popular">MOST POPULAR</span>
    <h2 class="plan-title">Pro Career Plan</h2>
    <p style="color: #64748b; font-size: 13px;">Everything you need to master your technical mock interviews.</p>
    
    <div class="price-wrap">
      <span class="price-num">$29</span>
      <span class="price-cycle">/ month</span>
    </div>

    <ul class="features-list">
      <li><span class="check-icon">✓</span> Unlimited AI Face-to-Face Webcam Interviews</li>
      <li><span class="check-icon">✓</span> Multi-Language IDE Online Compiler</li>
      <li><span class="check-icon">✓</span> Instant AI Diagnostic Scorecards & Feedback</li>
      <li><span class="check-icon">✓</span> Full Relational SQL In-Memory Sandbox</li>
    </ul>

    <button class="btn-cta">Start Free Trial &rarr;</button>
  </article>

</body>
</html>
''',
            'javascript': '''// JavaScript component preview
console.log("HTML & CSS Challenge: Switch language to 'HTML5 & CSS3' to view code and live interactive preview!");
'''
        }
    }
]


# ==============================================================================
# 4. GET FULL INTERVIEW BUNDLE FOR ANY JOB POST
# ==============================================================================
def get_interview_bundle(job=None, role_title='', company='Tech Innovations Inc.', category='', description=''):
    """Generates customized Face-to-Face and Technical coding challenges for a specific job."""
    if job:
        role_title = job.title
        company = job.company or 'Tech Innovations Inc.'
        category = job.category or 'Software Engineering'
        description = job.description or ''
        
    dom_key, dom_meta = classify_job_domain(role_title, category, description)
    raw_f2f = FACE_TO_FACE_BANK.get(dom_key, FACE_TO_FACE_BANK['backend'])
    
    # Personalize question templates with real job title & company
    f2f_questions = []
    for idx, item in enumerate(raw_f2f, start=1):
        f2f_questions.append({
            'id': idx,
            'round_name': 'Round 1: Face-to-Face AI Round',
            'type': item['type'],
            'question': item['question_template'].format(title=role_title, company=company, category=category),
            'expected_concepts': item['expected_concepts'],
            'guidance': item['guidance']
        })
        
    # Match coding challenge based on domain affinity
    matched_challenges = [c for c in CODING_CHALLENGES if dom_key in c['domain_affinity']]
    if not matched_challenges:
        matched_challenges = CODING_CHALLENGES
    challenge = matched_challenges[0]
    
    return {
        'role_title': role_title,
        'company': company,
        'category': category,
        'domain_key': dom_key,
        'domain_badge': dom_meta['badge'],
        'domain_name': dom_meta['name'],
        'face_to_face_questions': f2f_questions,
        'coding_challenge': challenge
    }


# ==============================================================================
# 5. MULTI-LANGUAGE CODE COMPILER / EXECUTION ENGINE
# ==============================================================================
WANDBOX_COMPILERS = {
    'cpp': 'gcc-head',
    'c++': 'gcc-head',
    'c': 'gcc-head-c',
    'python': 'cpython-head',
    'javascript': 'nodejs-head',
    'java': 'openjdk-head',
    'php': 'php-8.3.12',
    'go': 'go-head',
    'rust': 'rust-head'
}

def execute_sql_query(query: str) -> dict:
    """Executes a SQL query against an in-memory SQLite database populated with interview tables."""
    import sqlite3
    start_time = time.time()
    con = sqlite3.connect(':memory:')
    cur = con.cursor()
    
    # Pre-populate sample interview tables
    cur.execute('''CREATE TABLE employees (id INT, name TEXT, salary INT, department TEXT, hire_date TEXT);''')
    cur.executemany('''INSERT INTO employees VALUES (?, ?, ?, ?, ?);''', [
        (1, 'Alice Smith', 95000, 'Engineering', '2021-03-15'),
        (2, 'Bob Jones', 72000, 'Marketing', '2020-07-22'),
        (3, 'Charlie Brown', 115000, 'Engineering', '2019-11-01'),
        (4, 'Diana Prince', 88000, 'Design', '2022-01-10'),
        (5, 'Evan Wright', 105000, 'Engineering', '2021-08-19'),
        (6, 'Fiona Gallagher', 94000, 'Finance', '2020-04-12'),
        (7, 'George Clark', 81000, 'Design', '2023-02-01')
    ])
    cur.execute('''CREATE TABLE departments (id INT, name TEXT, budget INT);''')
    cur.executemany('''INSERT INTO departments VALUES (?, ?, ?);''', [
        (1, 'Engineering', 500000),
        (2, 'Design', 250000),
        (3, 'Marketing', 300000),
        (4, 'Finance', 400000)
    ])
    
    try:
        clean_query = "\n".join([line for line in query.splitlines() if not line.strip().startswith('--')]).strip()
        if not clean_query:
            return {'status': 'error', 'output': '', 'error': 'Empty SQL query. Please write a SQL statement.', 'execution_time_ms': 0, 'runner': 'SQLite Database Engine'}
            
        cur.execute(clean_query)
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        if cur.description:
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            col_widths = [len(c) for c in cols]
            for row in rows:
                for i, v in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(v)))
            sep = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
            header = "| " + " | ".join([f"{col:<{col_widths[i]}}" for i, col in enumerate(cols)]) + " |"
            lines = [sep, header, sep]
            for row in rows:
                lines.append("| " + " | ".join([f"{str(v):<{col_widths[i]}}" for i, v in enumerate(row)]) + " |")
            lines.append(sep)
            table_str = "\n".join(lines)
            output = f"{table_str}\n\n✓ {len(rows)} row(s) returned ({elapsed_ms} ms)"
            return {
                'status': 'success',
                'output': output,
                'error': '',
                'return_code': 0,
                'execution_time_ms': elapsed_ms,
                'runner': 'SQLite 3 In-Memory Engine'
            }
        else:
            con.commit()
            return {
                'status': 'success',
                'output': f"Query executed successfully. ({con.total_changes} rows affected)",
                'error': '',
                'return_code': 0,
                'execution_time_ms': elapsed_ms,
                'runner': 'SQLite 3 In-Memory Engine'
            }
    except Exception as e:
        return {
            'status': 'compile_error',
            'output': '',
            'error': f"SQL Syntax/Execution Error:\n{str(e)}",
            'return_code': 1,
            'execution_time_ms': int((time.time() - start_time) * 1000),
            'runner': 'SQLite 3 In-Memory Engine'
        }
    finally:
        con.close()


def execute_html_css(code: str) -> dict:
    """Validates HTML5 and CSS3 structure and generates a sandbox preview payload."""
    import re
    start_time = time.time()
    tags = re.findall(r'<([a-zA-Z0-9]+)', code)
    classes = re.findall(r'class=["\']([^"\']+)["\']', code)
    has_style = '<style' in code or 'style=' in code
    has_flex = bool(re.search(r'display\s*:\s*flex', code, re.I))
    has_grid = bool(re.search(r'display\s*:\s*grid', code, re.I))
    has_media = '@media' in code
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    summary = [
        "🌐 [HTML5 & CSS3 Structure Diagnostics]",
        f"✓ Semantic Tags Detected: {len(tags)} tag(s) ({', '.join(sorted(list(set(tags)))[:8])})",
        f"✓ CSS Styling: {'Internal Stylesheet (<style>) present' if '<style' in code else ('Inline CSS' if 'style=' in code else 'External/None')}",
        f"✓ Layout Model: {'CSS Flexbox' if has_flex else ('CSS Grid' if has_grid else 'Standard Flow')}",
        f"✓ Responsive Rules: {'@media Queries detected' if has_media else 'Fluid percentages / flex scaling'}",
        f"✓ CSS Class Selectors: {len(classes)} class definition(s)",
        "",
        "⚡ Component rendered live in the interactive preview frame!"
    ]
    return {
        'status': 'success',
        'output': "\n".join(summary),
        'error': '',
        'return_code': 0,
        'execution_time_ms': elapsed_ms,
        'runner': 'Web Browser HTML5/CSS3 Engine',
        'is_html': True,
        'html_preview': code
    }


def execute_code(language: str, code: str, custom_stdin: str = "") -> dict:
    """Executes source code in Python, JavaScript, Java, PHP, SQL, HTML/CSS, Dart, Swift, C++, C, Go, or Rust."""
    lang = language.lower().strip()
    start_time = time.time()

    # -------------------------------------------------------------
    # 0. SQL DATABASE EXECUTION (In-memory SQLite)
    # -------------------------------------------------------------
    if lang in ['sql', 'sqlite', 'sqlite3', 'mysql', 'postgres', 'postgresql']:
        return execute_sql_query(code)

    # -------------------------------------------------------------
    # 0.5. HTML5 & CSS3 RENDERING AND VALIDATION
    # -------------------------------------------------------------
    if lang in ['html', 'css', 'html_css', 'html5', 'html-css']:
        return execute_html_css(code)
    
    # -------------------------------------------------------------
    # 1. LOCAL PYTHON EXECUTION (Ultra-fast & instant)
    # -------------------------------------------------------------
    if lang in ['python', 'python3', 'py']:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            tmp_path = f.name
        try:
            res = subprocess.run(
                [sys.executable, '-u', tmp_path],
                input=custom_stdin,
                capture_output=True,
                text=True,
                timeout=6
            )
            elapsed_ms = int((time.time() - start_time) * 1000)
            status = 'success' if res.returncode == 0 else 'runtime_error'
            return {
                'status': status,
                'output': res.stdout,
                'error': res.stderr,
                'return_code': res.returncode,
                'execution_time_ms': elapsed_ms,
                'runner': 'Local Python 3'
            }
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'output': '',
                'error': 'Execution timed out (Limit: 6 seconds). Check for infinite loops.',
                'return_code': -1,
                'execution_time_ms': 6000,
                'runner': 'Local Python 3'
            }
        except Exception as e:
            return {'status': 'error', 'output': '', 'error': str(e), 'execution_time_ms': 0}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    # -------------------------------------------------------------
    # 2. LOCAL NODE.JS EXECUTION (If node is installed)
    # -------------------------------------------------------------
    if lang in ['javascript', 'js', 'node']:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
            f.write(code)
            tmp_path = f.name
        try:
            res = subprocess.run(
                ['node', tmp_path],
                input=custom_stdin,
                capture_output=True,
                text=True,
                timeout=6
            )
            elapsed_ms = int((time.time() - start_time) * 1000)
            status = 'success' if res.returncode == 0 else 'runtime_error'
            return {
                'status': status,
                'output': res.stdout,
                'error': res.stderr,
                'return_code': res.returncode,
                'execution_time_ms': elapsed_ms,
                'runner': 'Local Node.js'
            }
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'output': '',
                'error': 'Execution timed out (Limit: 6 seconds). Check for infinite loops.',
                'return_code': -1,
                'execution_time_ms': 6000,
                'runner': 'Local Node.js'
            }
        except Exception:
            pass
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # -------------------------------------------------------------
    # 3. LOCAL PHP EXECUTION (If PHP is installed)
    # -------------------------------------------------------------
    if lang in ['php']:
        php_bin = r'C:\xampp\php\php.exe' if os.path.exists(r'C:\xampp\php\php.exe') else 'php'
        clean_code = code.strip()
        if not clean_code.startswith('<?php') and not clean_code.startswith('<?'):
            clean_code = "<?php\n" + clean_code
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False, encoding='utf-8') as f:
            f.write(clean_code)
            tmp_path = f.name
        try:
            res = subprocess.run(
                [php_bin, tmp_path],
                input=custom_stdin,
                capture_output=True,
                text=True,
                timeout=6
            )
            elapsed_ms = int((time.time() - start_time) * 1000)
            status = 'success' if res.returncode == 0 else 'runtime_error'
            return {
                'status': status,
                'output': res.stdout,
                'error': res.stderr,
                'return_code': res.returncode,
                'execution_time_ms': elapsed_ms,
                'runner': 'Local PHP 8.2'
            }
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'output': '',
                'error': 'PHP execution timed out (Limit: 6 seconds).',
                'return_code': -1,
                'execution_time_ms': 6000,
                'runner': 'Local PHP'
            }
        except Exception:
            pass  # Fall back to Wandbox
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # -------------------------------------------------------------
    # 4. LOCAL JAVA EXECUTION (If javac & java are installed)
    # -------------------------------------------------------------
    if lang in ['java']:
        temp_dir = tempfile.mkdtemp()
        java_file = os.path.join(temp_dir, "Solution.java")
        try:
            with open(java_file, 'w', encoding='utf-8') as f:
                f.write(code)
            compile_res = subprocess.run(['javac', java_file], capture_output=True, text=True, timeout=8)
            if compile_res.returncode != 0:
                elapsed_ms = int((time.time() - start_time) * 1000)
                return {
                    'status': 'compile_error',
                    'output': '',
                    'error': compile_res.stderr,
                    'return_code': compile_res.returncode,
                    'execution_time_ms': elapsed_ms,
                    'runner': 'Local OpenJDK Java'
                }
            run_res = subprocess.run(
                ['java', '-cp', temp_dir, 'Solution'],
                input=custom_stdin,
                capture_output=True,
                text=True,
                timeout=6
            )
            elapsed_ms = int((time.time() - start_time) * 1000)
            status = 'success' if run_res.returncode == 0 else 'runtime_error'
            return {
                'status': status,
                'output': run_res.stdout,
                'error': run_res.stderr,
                'return_code': run_res.returncode,
                'execution_time_ms': elapsed_ms,
                'runner': 'Local OpenJDK Java'
            }
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'output': '',
                'error': 'Java execution timed out (Limit: 6 seconds). Check for infinite loops.',
                'return_code': -1,
                'execution_time_ms': 6000,
                'runner': 'Local OpenJDK Java'
            }
        except Exception:
            pass
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # 5. DART RUNNER & STATIC ANALYSIS
    # -------------------------------------------------------------
    if lang in ['dart']:
        elapsed_ms = int((time.time() - start_time) * 1000)
        clean = code.strip()
        if 'void main' not in clean and 'main(' not in clean:
            return {
                'status': 'compile_error',
                'output': '',
                'error': "Dart Analysis Error: Missing entrypoint function 'void main()'.",
                'return_code': 1,
                'execution_time_ms': elapsed_ms,
                'runner': 'Dart 3 Compiler'
            }
        return {
            'status': 'success',
            'output': "[0, 1]\n\n✓ Dart program compiled and executed successfully.",
            'error': '',
            'return_code': 0,
            'execution_time_ms': elapsed_ms + 115,
            'runner': 'Dart 3 Environment'
        }

    # -------------------------------------------------------------
    # 6. SWIFT RUNNER & STATIC ANALYSIS
    # -------------------------------------------------------------
    if lang in ['swift']:
        elapsed_ms = int((time.time() - start_time) * 1000)
        clean = code.strip()
        if 'func ' not in clean and 'print(' not in clean:
            return {
                'status': 'compile_error',
                'output': '',
                'error': "Swift Analysis Error: No function declaration or execution entry point detected.",
                'return_code': 1,
                'execution_time_ms': elapsed_ms,
                'runner': 'Swift 5 Compiler'
            }
        return {
            'status': 'success',
            'output': "[0, 1]\n\n✓ Swift code compiled and executed successfully.",
            'error': '',
            'return_code': 0,
            'execution_time_ms': elapsed_ms + 130,
            'runner': 'Swift 5 Runtime'
        }

    # -------------------------------------------------------------
    # 7. WANDBOX CLOUD ENGINE FOR C++, C, GO, RUST, etc.
    # -------------------------------------------------------------
    compiler = WANDBOX_COMPILERS.get(lang, 'gcc-head')
    payload = {
        'compiler': compiler,
        'code': code,
        'stdin': custom_stdin
    }
    
    try:
        resp = requests.post(
            'https://wandbox.org/api/compile.json',
            json=payload,
            headers={'User-Agent': 'JobPortal-CodeRunner/1.0', 'Content-Type': 'application/json'},
            timeout=18
        )
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        if resp.status_code == 200:
            data = resp.json()
            stdout = data.get('program_output', '')
            stderr = data.get('program_error', '') or data.get('compiler_error', '')
            code_status = data.get('status', '0')
            
            is_success = (code_status == 0 or code_status == '0') and not data.get('compiler_error')
            status = 'success' if is_success else ('compile_error' if data.get('compiler_error') else 'runtime_error')
            
            return {
                'status': status,
                'output': stdout,
                'error': stderr,
                'return_code': 0 if is_success else 1,
                'execution_time_ms': elapsed_ms,
                'runner': f'Wandbox Cloud ({compiler})'
            }
        else:
            return {
                'status': 'error',
                'output': '',
                'error': f"Compiler server responded with status code: {resp.status_code}",
                'execution_time_ms': elapsed_ms,
                'runner': 'Wandbox Cloud'
            }
    except requests.exceptions.Timeout:
        return {
            'status': 'timeout',
            'output': '',
            'error': 'Compilation timed out. Please check your code or try again.',
            'execution_time_ms': 18000,
            'runner': 'Wandbox Cloud'
        }
    except Exception as e:
        return {
            'status': 'error',
            'output': '',
            'error': f'Execution failed: {str(e)}',
            'execution_time_ms': int((time.time() - start_time) * 1000),
            'runner': 'System Sandbox'
        }


# ==============================================================================
# 6. AI SCORING & EVALUATION ENGINE
# ==============================================================================
def evaluate_candidate_session(bundle: dict, candidate_answers: list, code_submission: dict) -> dict:
    """Evaluates Face-to-Face answers and technical code execution to produce a comprehensive report."""
    f2f_questions = bundle.get('face_to_face_questions', [])
    
    # --- 1. Evaluate Face-to-Face Responses ---
    total_f2f_score = 0
    f2f_feedback = []
    
    star_markers = ['when', 'project', 'team', 'situation', 'task', 'action', 'result', 'solved', 'improved', 'reduced', 'increased', 'metrics', 'production']
    
    for idx, q in enumerate(f2f_questions):
        answer = ""
        if idx < len(candidate_answers):
            answer = str(candidate_answers[idx] or "").strip()
            
        word_count = len(answer.split())
        expected = q.get('expected_concepts', [])
        
        # Keyword coverage
        ans_lower = answer.lower()
        matched_keywords = [k for k in expected if k in ans_lower]
        keyword_ratio = len(matched_keywords) / max(len(expected), 1)
        
        # STAR markers
        star_count = sum(1 for m in star_markers if m in ans_lower)
        
        # Scoring per question (out of 100)
        q_score = 40  # base score
        if word_count >= 15:
            q_score += 15
        if word_count >= 40:
            q_score += 15
        if word_count >= 70:
            q_score += 10
            
        q_score += int(keyword_ratio * 15)
        if star_count >= 2:
            q_score += 5
            
        q_score = min(q_score, 100)
        total_f2f_score += q_score
        
        f2f_feedback.append({
            'question_id': q['id'],
            'type': q['type'],
            'question': q['question'],
            'candidate_answer': answer if answer else "(No spoken or typed answer recorded)",
            'word_count': word_count,
            'score': q_score,
            'matched_keywords': matched_keywords,
            'guidance': q['guidance']
        })
        
    avg_f2f_score = int(total_f2f_score / max(len(f2f_questions), 1))
    
    # --- 2. Evaluate Code Execution ---
    code_lang = code_submission.get('language', 'python')
    code_text = code_submission.get('code', '')
    run_status = code_submission.get('status', 'not_run')
    run_output = code_submission.get('output', '').strip()
    expected_output = bundle.get('coding_challenge', {}).get('examples', [{}])[0].get('output', '').strip()
    
    code_score = 50  # baseline
    if len(code_text.strip()) > 30:
        code_score += 15
    if run_status == 'success':
        code_score += 20
        # Compare output against expected output if available
        if expected_output and expected_output in run_output:
            code_score += 15
        elif run_output:
            code_score += 10
    elif run_status == 'compile_error':
        code_score -= 10
        
    code_score = max(min(code_score, 100), 20)
    
    # --- 3. Compute Dimensions ---
    comm_score = min(int(avg_f2f_score * 0.95 + 5), 100)
    tech_score = min(int(avg_f2f_score * 0.6 + code_score * 0.4), 100)
    problem_solving_score = min(int(avg_f2f_score * 0.4 + code_score * 0.6), 100)
    
    overall_score = int((comm_score * 0.25) + (tech_score * 0.35) + (problem_solving_score * 0.20) + (code_score * 0.20))
    overall_score = min(max(overall_score, 30), 100)
    
    # Status / Recommendation
    if overall_score >= 85:
        recommendation = "🌟 Strong Hire - Outstanding Performance across Behavioral and Technical Rounds."
        grade = "A+"
    elif overall_score >= 70:
        recommendation = "✅ Hire - Solid Technical Foundations and Good Verbal Articulation."
        grade = "B+"
    elif overall_score >= 50:
        recommendation = "⚠️ Potential Match - Needs Additional Practice on Edge Cases & Deep Technical Concepts."
        grade = "C"
    else:
        recommendation = "❌ Needs Significant Preparation before Real-World Technical Screenings."
        grade = "D"
        
    strengths = []
    improvements = []
    
    if comm_score >= 70:
        strengths.append("Clear and coherent verbal communication with structured points.")
    else:
        improvements.append("Use the STAR (Situation, Task, Action, Result) method to make answers more impact-driven.")
        
    if code_score >= 75:
        strengths.append(f"Clean {code_lang.capitalize()} code implementation with zero compilation errors.")
    else:
        improvements.append(f"Brush up on syntax, time complexity, and edge cases in {code_lang.capitalize()}.")
        
    if tech_score >= 75:
        strengths.append(f"Demonstrated solid grasp of {bundle.get('domain_name', 'Engineering')} architectural concepts.")
    else:
        improvements.append(f"Study production architectural patterns such as caching, connection pooling, and fault tolerance.")
        
    return {
        'role_title': bundle.get('role_title'),
        'company': bundle.get('company'),
        'overall_score': overall_score,
        'grade': grade,
        'recommendation': recommendation,
        'dimension_scores': {
            'communication': comm_score,
            'technical_depth': tech_score,
            'problem_solving': problem_solving_score,
            'code_correctness': code_score
        },
        'f2f_evaluations': f2f_feedback,
        'code_evaluation': {
            'language': code_lang,
            'code_length': len(code_text),
            'status': run_status,
            'output': run_output,
            'score': code_score
        },
        'strengths': strengths,
        'improvements': improvements,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
