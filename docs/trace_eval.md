# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Đào Đức Anh  
> **Mã Sinh Viên / Mã Học viên:** 2A202602567  
> **Chủ đề Lựa chọn:** Roadmap Agent

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá           | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm                                      |
| :-------------------------- | :------------: | :----------------------------------------------------------------------- |
| **1. Multi-step Reasoning** |     5 / 5      | Bài toán có yêu cầu chia nhỏ nhiều bước suy luận nối tiếp nhau không?    |
| **2. Tool Interaction**     |     5 / 5      | Hệ thống có cần kết nối với MCP Server / Cơ sở dữ liệu bên ngoài không?  |
| **3. Dynamic Decision**     |     5 / 5      | Bước tiếp theo có phụ thuộc vào kết quả quan sát bước trước không?       |
| **4. Long Horizon Goal**    |     5 / 5      | Hệ thống có phải giữ mục tiêu xuyên suốt qua nhiều lượt xử lý không?     |
| **TỔNG ĐIỂM AGENTIC FIT**   |  **20 / 20**   | _Nếu tổng điểm > 12/20: Bài toán rất phù hợp triển khai Agentic System._ |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "action_type": "UNDERSTAND_GOAL",
    "input": {
      "topic": "AWS Cloud",
      "goal": "I want to learn AWS from beginner to intermediate and focus on practical cloud fundamentals.",
      "level": "BEGINNER",
      "constraints": {
        "hoursPerDay": 1.0,
        "deadlineWeeks": 6
      }
    },
    "thought": "Analyze the goal, level, and constraints before creating the roadmap."
  },
  {
    "step": 2,
    "action_type": "PLAN_ROADMAP",
    "input": {
      "topic": "AWS Cloud",
      "goal": "I want to learn AWS from beginner to intermediate and focus on practical cloud fundamentals.",
      "level": "BEGINNER",
      "constraints": {
        "hoursPerDay": 1.0,
        "deadlineWeeks": 6
      }
    },
    "output": {
      "title": "AWS Cloud Fundamentals Roadmap",
      "topic": "AWS Cloud",
      "areas": [
        "Introduction to Cloud Computing",
        "Getting Started with AWS",
        "Core AWS Services Overview",
        "Deploying a Simple Web Application",
        "Data Storage Solutions in AWS",
        "Monitoring and Security in AWS",
        "Cost Management and Optimization"
      ]
    },
    "latency_ms": 10132.87
  },
  {
    "step": 3,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "search_resources",
    "arguments": {
      "query": "AWS Cloud Introduction to Cloud Computing",
      "topic": "AWS Cloud",
      "level": "BEGINNER",
      "max_results": 3
    },
    "observation": {
      "status": "SUCCESS",
      "query": "AWS Cloud Introduction to Cloud Computing",
      "topic": "AWS Cloud",
      "results": [
        {
          "resource_id": "live-6357224136338779785-1",
          "title": "Introduction to Cloud Computing on AWS for Beginners [2026]",
          "url": "https://www.udemy.com/course/introduction-to-cloud-computing-on-amazon-aws-for-beginners",
          "type": "ARTICLE",
          "description": "## Requirements\n\n## Description\n\nThis beginner-friendly Introduction to Cloud Computing on AWS course takes you from the AWS basics to becoming a competent AWS cloud practitioner. With expert instruction and engaging content, you'll learn general cloud computing concepts and AWS ",
          "source": "www.udemy.com",
          "level": "UNKNOWN",
          "score": 3
        },
        {
          "resource_id": "live-7224833391422995275-2",
          "title": "Introduction to AWS for Cloud Beginners | Coursera",
          "url": "https://www.coursera.org/learn/introduction-to-aws-for-cloud-beginners",
          "type": "ARTICLE",
          "description": "Get Coursera Plus\n\n  ![₹13,999 ₹7,499/year\n  [Microsoft, Google, Meta, and Stanford logos]\n  ](\n Coursera for teams logo\n\n  ### Start with easy savings for hard-working teams\n\n  Save 30% today\n\n  30% off team training\n\n## Frequently asked questions\n\nAWS (Amazon Web Services) is a",
          "source": "www.coursera.org",
          "level": "UNKNOWN",
          "score": 2
        },
        {
          "resource_id": "live-8308511564701084787-3",
          "title": "What is cloud computing? - Overview of Amazon Web Services",
          "url": "https://docs.aws.amazon.com/whitepapers/latest/aws-overview/what-is-cloud-computing.html",
          "type": "ARTICLE",
          "description": "Cloud computing is the on-demand delivery of compute power, database, storage, applications, and other IT resources through a cloud services platform via the internet with pay-as-you-go pricing. Whether you are running applications that share photos to millions of mobile users or",
          "source": "docs.aws.amazon.com",
          "level": "UNKNOWN",
          "score": 1
        }
      ],
      "source_mode": "tavily"
    },
    "latency_ms": 3183.61
  },
  {
    "step": 4,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "get_resource_details",
    "arguments": {
      "resource_id": "live-6357224136338779785-1"
    },
    "observation": {
      "status": "SUCCESS",
      "resource": {
        "resource_id": "live-6357224136338779785-1",
        "title": "Introduction to Cloud Computing on AWS for Beginners [2026]",
        "url": "https://www.udemy.com/course/introduction-to-cloud-computing-on-amazon-aws-for-beginners",
        "type": "ARTICLE",
        "description": "## Requirements\n\n## Description\n\nThis beginner-friendly Introduction to Cloud Computing on AWS course takes you from the AWS basics to becoming a competent AWS cloud practitioner. With expert instruction and engaging content, you'll learn general cloud computing concepts and AWS ",
        "source": "www.udemy.com",
        "level": "UNKNOWN",
        "score": 3
      }
    },
    "latency_ms": 0.03
  },
  {
    "step": 5,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "search_resources",
    "arguments": {
      "query": "AWS Cloud Getting Started with AWS",
      "topic": "AWS Cloud",
      "level": "BEGINNER",
      "max_results": 3
    },
    "observation": {
      "status": "SUCCESS",
      "query": "AWS Cloud Getting Started with AWS",
      "topic": "AWS Cloud",
      "results": [
        {
          "resource_id": "live-6292063644866853506-1",
          "title": "Getting Started with AWS Cloud Essentials",
          "url": "https://aws.amazon.com/getting-started/cloud-essentials",
          "type": "ARTICLE",
          "description": "The AWS Cloud encompasses a broad set of global cloud-based products that includes compute, storage, databases, analytics, networking, mobile, developer tools, management tools, IoT, security, and enterprise applications: on-demand, available in seconds, with pay-as-you-go pricin",
          "source": "aws.amazon.com",
          "level": "UNKNOWN",
          "score": 3
        },
        {
          "resource_id": "live-1027016956154000750-2",
          "title": "Getting Started With AWS Cloud | Step-by-Step Guide",
          "url": "https://www.youtube.com/watch?v=CjKhQoYeR4Q",
          "type": "ARTICLE",
          "description": "# Getting Started With AWS Cloud | Step-by-Step Guide\n## Travis Media\n330000 subscribers\n5418 likes\n\n### Description\n203422 views\nPosted: 30 Apr 2023\nAll developers and inspiring developers should be cloud competent. This means creating an account and getting your hands dirty. \n\n",
          "source": "www.youtube.com",
          "level": "UNKNOWN",
          "score": 2
        },
        {
          "resource_id": "live-5929316419476607488-3",
          "title": "AWS Cloud Get Started",
          "url": "https://www.w3schools.com/aws/aws_cloudessentials_getstarted.php",
          "type": "ARTICLE",
          "description": "## AWS Cert\n\nAWS Certificate   \n\n## AWS Examples\n\nAWS Cloud Exercises AWS Cloud Quiz   \n\n## More AWS\n\nAWS Machine Learning AWS Serverless AWS GenAI\n\n# AWS Cloud Get Started\n\n❮ Previous Next ❯\n\nShare\n\n## Free AWS Account\n\nAWS offers a Free Tier with limited usage of services at no",
          "source": "www.w3schools.com",
          "level": "UNKNOWN",
          "score": 1
        }
      ],
      "source_mode": "tavily"
    },
    "latency_ms": 5914.17
  },
  {
    "step": 6,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "get_resource_details",
    "arguments": {
      "resource_id": "live-6292063644866853506-1"
    },
    "observation": {
      "status": "SUCCESS",
      "resource": {
        "resource_id": "live-6292063644866853506-1",
        "title": "Getting Started with AWS Cloud Essentials",
        "url": "https://aws.amazon.com/getting-started/cloud-essentials",
        "type": "ARTICLE",
        "description": "The AWS Cloud encompasses a broad set of global cloud-based products that includes compute, storage, databases, analytics, networking, mobile, developer tools, management tools, IoT, security, and enterprise applications: on-demand, available in seconds, with pay-as-you-go pricin",
        "source": "aws.amazon.com",
        "level": "UNKNOWN",
        "score": 3
      }
    },
    "latency_ms": 0.04
  },
  {
    "step": 7,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "search_resources",
    "arguments": {
      "query": "AWS Cloud Core AWS Services Overview",
      "topic": "AWS Cloud",
      "level": "BEGINNER",
      "max_results": 3
    },
    "observation": {
      "status": "SUCCESS",
      "query": "AWS Cloud Core AWS Services Overview",
      "topic": "AWS Cloud",
      "results": [
        {
          "resource_id": "live-8760404890029629928-1",
          "title": "Introduction to AWS Core Services | AWS Introduction | Overview of AWS Core Services | What is AWS",
          "url": "https://www.youtube.com/watch?v=BUKgR26lwvE",
          "type": "ARTICLE",
          "description": "In this video, we’ll explore:\n1️⃣ Compute Services – Learn about Amazon EC2, Lambda, and container orchestration with ECS and EKS.\n2️⃣ Storage Services – Discover how Amazon S3, EBS, and EFS make storing and accessing data effortless.\n3️⃣ Database Services – Dive into relational ",
          "source": "www.youtube.com",
          "level": "UNKNOWN",
          "score": 3
        },
        {
          "resource_id": "live-6108194573396403316-2",
          "title": "AWS Core Services: What You Need To Know - Clarusway",
          "url": "https://clarusway.com/aws-core-services",
          "type": "ARTICLE",
          "description": "AWS cloud services allow different organizations to be more effective in their execution of IT tasks. They can establish secure yet affordable systems for scalable servers, compute solutions, and databases with the power of those services. The Amazon Web Service is a leading clou",
          "source": "clarusway.com",
          "level": "UNKNOWN",
          "score": 2
        },
        {
          "resource_id": "live-5220828605718736798-3",
          "title": "AWS Core Services | Coursera",
          "url": "https://www.coursera.org/learn/aws-core-services",
          "type": "ARTICLE",
          "description": "30% off team training\n\n## Frequently asked questions\n\nThis course provides an overview of cloud computing and the AWS ecosystem. It covers key AWS services, including Identity and Access Management (IAM) for secure access control and Amazon EC2 for scalable computing resources. L",
          "source": "www.coursera.org",
          "level": "UNKNOWN",
          "score": 1
        }
      ],
      "source_mode": "tavily"
    },
    "latency_ms": 4210.81
  },
  {
    "step": 8,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "search_resources",
    "arguments": {
      "query": "AWS Cloud Deploying a Simple Web Application",
      "topic": "AWS Cloud",
      "level": "BEGINNER",
      "max_results": 3
    },
    "observation": {
      "status": "SUCCESS",
      "query": "AWS Cloud Deploying a Simple Web Application",
      "topic": "AWS Cloud",
      "results": [
        {
          "resource_id": "live-5776654913875202788-1",
          "title": "Web Application Hosting in the AWS Cloud - DEV Community",
          "url": "https://dev.to/awsmenacommunity/web-application-hosting-in-the-aws-cloud-19j3",
          "type": "ARTICLE",
          "description": "### Consider automated deployment\n\n Amazon Lightsail : Simple app development VPS with everything needed to build a Web app or website. Ideal for simple workloads and quick deployments.\n AWS Elastic Beanstalk : Easy-to-use service for deploying and scaling web apps developed with",
          "source": "dev.to",
          "level": "UNKNOWN",
          "score": 3
        },
        {
          "resource_id": "live-5257933233612649832-2",
          "title": "The Ultimate Guide to Hosting Web Applications on AWS | Cloud Deployment",
          "url": "https://www.oneclickitsolution.com/centerofexcellence/devops/complete-guide-to-hosting-web-applications-on-aws-cloud",
          "type": "ARTICLE",
          "description": "# The Complete Guide to Hosting Web Applications on AWS Cloud. Here’s a more detailed breakdown of AWS web hosting options, their use cases, estimated pricing and key benefits:. ## Amazon S3 (Static Website Hosting). * **Description:** Amazon S3 (Simple Storage Service) can host ",
          "source": "www.oneclickitsolution.com",
          "level": "UNKNOWN",
          "score": 2
        },
        {
          "resource_id": "live-3175090827711953978-3",
          "title": "Deploy a Web App on AWS Like a Pro: Beginner to Advance",
          "url": "https://www.youtube.com/watch?v=rezvilAddDs",
          "type": "ARTICLE",
          "description": "# Deploy a Web App on AWS Like a Pro: Beginner to Advance\n## CodeGenitor\n16300 subscribers\n105 likes\n\n### Description\n3582 views\nPosted: 15 Mar 2025\nDeploying a Simple Web App on AWS – Manual Setup Tutorial\nConnect with Me: \n\nWelcome to a hands-on tutorial where we walk you throu",
          "source": "www.youtube.com",
          "level": "UNKNOWN",
          "score": 1
        }
      ],
      "source_mode": "tavily"
    },
    "latency_ms": 6861.44
  },
  {
    "step": 9,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "search_resources",
    "arguments": {
      "query": "AWS Cloud Data Storage Solutions in AWS",
      "topic": "AWS Cloud",
      "level": "BEGINNER",
      "max_results": 3
    },
    "observation": {
      "status": "SUCCESS",
      "query": "AWS Cloud Data Storage Solutions in AWS",
      "topic": "AWS Cloud",
      "results": [
        {
          "resource_id": "live-2637290748954581435-1",
          "title": "Cloud Storage Services on AWS",
          "url": "https://aws.amazon.com/products/storage",
          "type": "ARTICLE",
          "description": "## Why Cloud Storage on AWS?\n\nMillions of customers use AWS cloud storage services to transform their business, increase agility, reduce costs, and accelerate innovation. Choose from a broad portfolio of storage solutions with deep functionality for storing, accessing, protecting",
          "source": "aws.amazon.com",
          "level": "UNKNOWN",
          "score": 3
        },
        {
          "resource_id": "live-2825083059347253894-2",
          "title": "AWS Cloud Storage | Amazon Web Services",
          "url": "https://www.youtube.com/watch?v=aYH-0Fr3ahs",
          "type": "ARTICLE",
          "description": "# AWS Cloud Storage | Amazon Web Services\n## Amazon Web Services\n846000 subscribers\n34 likes\n\n### Description\n1561 views\nPosted: 14 Apr 2025\nDiscover why millions of customers use AWS Cloud Storage to transform their business, increase agility, reduce costs, and accelerate innova",
          "source": "www.youtube.com",
          "level": "UNKNOWN",
          "score": 2
        },
        {
          "resource_id": "live-8878094460224031367-3",
          "title": "AWS Storage category iconStorage - Overview of Amazon Web Services",
          "url": "https://docs.aws.amazon.com/whitepapers/latest/aws-overview/storage-services.html",
          "type": "ARTICLE",
          "description": "The AWS Storage Gateway is a hybrid storage\nservice that allows your on-premises applications to seamlessly use AWS cloud storage. You can\nuse the service for backup and archiving, disaster recovery, cloud data processing, storage\ntiering, and migration. Your applications connect",
          "source": "docs.aws.amazon.com",
          "level": "UNKNOWN",
          "score": 1
        }
      ],
      "source_mode": "tavily"
    },
    "latency_ms": 6024.96
  },
  {
    "step": 10,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "search_resources",
    "arguments": {
      "query": "AWS Cloud Monitoring and Security in AWS",
      "topic": "AWS Cloud",
      "level": "BEGINNER",
      "max_results": 3
    },
    "observation": {
      "status": "SUCCESS",
      "query": "AWS Cloud Monitoring and Security in AWS",
      "topic": "AWS Cloud",
      "results": [
        {
          "resource_id": "live-3445487363991227469-1",
          "title": "Monitoring and Logging - Introduction to AWS Security",
          "url": "https://docs.aws.amazon.com/whitepapers/latest/introduction-aws-security/monitoring-and-logging.html",
          "type": "ARTICLE",
          "description": "With AWS CloudTrail, you can monitor your AWS deployments in the cloud by getting a history of AWS API calls for your account, including API calls made via the AWS Management Console, the AWS SDKs, the command line tools, and higher-level AWS services. You can also identify which",
          "source": "docs.aws.amazon.com",
          "level": "UNKNOWN",
          "score": 3
        },
        {
          "resource_id": "live-2555091831836294446-2",
          "title": "Understanding the AWS Cloud Security Model - GeeksforGeeks",
          "url": "https://www.geeksforgeeks.org/cloud-computing/security-model-of-aws-cloud",
          "type": "ARTICLE",
          "description": "Monitoring and Logging: Amazon CloudWatch, coupled with AWS CloudTrail, provides real-time monitoring and logging of AWS resources, among other services. These services offer insight into account events, consuming resources, and security breaches enabling quick detection and resp",
          "source": "www.geeksforgeeks.org",
          "level": "UNKNOWN",
          "score": 2
        },
        {
          "resource_id": "live-3859015500629984517-3",
          "title": "What is AWS monitoring?",
          "url": "https://www.sumologic.com/glossary/aws-monitoring",
          "type": "ARTICLE",
          "description": "### A guide to AWS monitoring and security tools\n\nTo help meet the cloud reliability and security needs of its customers, AWS offers a range of tools that IT organizations can use to monitor and secure their AWS cloud environments. These tools are available on a pay-per-use basis",
          "source": "www.sumologic.com",
          "level": "UNKNOWN",
          "score": 1
        }
      ],
      "source_mode": "tavily"
    },
    "latency_ms": 10362.34
  },
  {
    "step": 11,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "search_resources",
    "arguments": {
      "query": "AWS Cloud Cost Management and Optimization",
      "topic": "AWS Cloud",
      "level": "BEGINNER",
      "max_results": 3
    },
    "observation": {
      "status": "SUCCESS",
      "query": "AWS Cloud Cost Management and Optimization",
      "topic": "AWS Cloud",
      "results": [
        {
          "resource_id": "live-2849193258972833933-1",
          "title": "AWS Cloud Cost Optimization: 5 Proven Strategies",
          "url": "https://www.harness.io/blog/5-essential-aws-cloud-cost-optimization-strategies",
          "type": "ARTICLE",
          "description": "The AWS cost management process involves the following:\n\n1. Cost Visibility: Continuously improving visibility into cloud expenditures to understand spending patterns and identify cost drivers.\n2. Resource Optimization: Selecting and allocating just enough computing power, storag",
          "source": "www.harness.io",
          "level": "UNKNOWN",
          "score": 3
        },
        {
          "resource_id": "live-524861608011288272-2",
          "title": "AWS Cloud Cost Optimization: Tools, Strategies, Best Practices",
          "url": "https://www.cloudzero.com/blog/aws-cost-optimization-tools",
          "type": "ARTICLE",
          "description": "Quick answer: AWS cloud cost optimization is the ongoing practice of reducing waste and improving spend efficiency across Amazon Web Services infrastructure, including EC2, S3, RDS, and data transfer. The core levers are rightsizing overprovisioned resources, extending commitment",
          "source": "www.cloudzero.com",
          "level": "UNKNOWN",
          "score": 2
        },
        {
          "resource_id": "live-5834450163769573305-3",
          "title": "AWS Cloud Cost Management Tools: Comprehensive Buyer’s Guide (2026)",
          "url": "https://newrelic.com/blog/observability/aws-cloud-cost-management-tools",
          "type": "ARTICLE",
          "description": "## Understanding AWS cloud cost management\n\nAWS cloud cost management is the practice of monitoring, allocating, and optimizing what you spend running workloads on Amazon Web Services. It covers tracking spend across accounts and services, attributing costs to the teams or produc",
          "source": "newrelic.com",
          "level": "UNKNOWN",
          "score": 1
        }
      ],
      "source_mode": "tavily"
    },
    "latency_ms": 13501.11
  },
  {
    "step": 12,
    "action_type": "VALIDATE_ROADMAP",
    "roadmap_id": "roadmap_73a1a68972",
    "output": {
      "nodes": 9,
      "edges": 12
    },
    "latency_ms": 0.02
  },
  {
    "step": 13,
    "action_type": "SAVE_ROADMAP",
    "roadmap_id": "roadmap_73a1a68972",
    "output": {
      "status": "DRAFT",
      "storage": "/home/ducanh/Documents/AI20K/Lab/Day 3/K4-DAY03-DaoDucAnh-2A202602567/data/roadmaps.json"
    },
    "latency_ms": 5.61
  },
  {
    "step": 14,
    "action_type": "FINAL_ANSWER",
    "roadmap_id": "roadmap_73a1a68972",
    "output": {
      "title": "AWS Cloud Fundamentals Roadmap",
      "lesson_count": 7,
      "checkpoint_count": 2
    },
    "thought": "Return a persisted draft roadmap with deterministic checkpoint state."
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [ x ] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 44 lượt.
- **Kết quả đẩy Repo nộp bài:** [ x ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
