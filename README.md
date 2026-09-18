# SO-101 Robot Demonstration

## Overview

I built an end-to-end robot learning pipeline using the **SO-101 leader-follower system** to collect demonstrations, construct training datasets, fine-tune VLA models, and deploy learned policies on the physical robot.

The current setup focuses on object manipulation tasks such as **locating, reaching, and picking up objects from a text instructions**.

## Key Components

- Collected **200 real-robot demonstrations** using SO-101 leader-follower teleoperation.
- Recorded observations from:
  - Third-person RGB camera
  - Wrist-mounted RGB camera
  - Robot proprioception
- Built and converted the dataset for VLA training using **LeRobot, TFDS, and RLDS**.
- Fine-tuned **OpenVLA** and **OpenVLA-OFT** for the SO-101 manipulation setup.
- Deployed learned policies on the physical SO-101 follower arm.

## System Setup

| Component | Configuration |
|---|---|
| Robot | SO-101 Leader + Follower |
| Task | Object manipulation / pick-and-place |
| Models | OpenVLA, OpenVLA-OFT |
| Visual Input | Third-person + wrist RGB cameras |
| Robot State | Joint proprioception |
| Action Space | SO-101 joint actions |
| Frameworks | LeRobot, PyTorch, Hugging Face, TensorFlow Datasets |

## Research

This setup is being used to study deployment-time robustness in Vision-Language-Action models.

## Demo
