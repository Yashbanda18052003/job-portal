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
        'keywords': ['mobile', 'android', 'ios', 'swift', 'kotlin', 'flutter', 'react native'],
        'name': 'Mobile Development',
        'badge': '📱 Mobile Engineering'
    }
}

def classify_job_domain(title='', category='', description=''):
    """Classifies a job into a technical domain based on title, category, and description."""
    text = f"{title} {category} {description}".lower()
    
    scores = {}
    for dom_key, dom_data in DOMAINS.items():
        score = 0
        for kw in dom_data['keywords']:
            if kw in text:
                # Title matches have 3x weight
                if kw in title.lower():
                    score += 3
                elif kw in category.lower():
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
    'go': 'go-head',
    'rust': 'rust-head'
}

def execute_code(language: str, code: str, custom_stdin: str = "") -> dict:
    """Executes source code in Python, JavaScript, Java, C++, C, Go, or Rust."""
    lang = language.lower().strip()
    start_time = time.time()
    
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
            # Fall back to Wandbox if local node failed
            pass
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # -------------------------------------------------------------
    # 3. LOCAL JAVA EXECUTION (If javac & java are installed)
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
            pass # Fallback to Wandbox
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # 4. WANDBOX CLOUD ENGINE FOR C++, C, GO, RUST, etc.
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
