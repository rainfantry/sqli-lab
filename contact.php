<?php
header('Content-Type: application/json');

// Rate limit: 1 submission per 30 seconds per IP
$ip = $_SERVER['REMOTE_ADDR'];
$lockfile = sys_get_temp_dir() . '/contact_' . md5($ip) . '.lock';
if (file_exists($lockfile) && (time() - filemtime($lockfile)) < 30) {
    echo json_encode(['ok' => false, 'error' => 'Please wait 30 seconds between submissions.']);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo json_encode(['ok' => false, 'error' => 'Invalid request.']);
    exit;
}

$category = strip_tags(trim($_POST['category'] ?? ''));
$name     = strip_tags(trim($_POST['name'] ?? ''));
$email    = filter_var(trim($_POST['email'] ?? ''), FILTER_VALIDATE_EMAIL);
$phone    = strip_tags(trim($_POST['phone'] ?? ''));
$message  = strip_tags(trim($_POST['message'] ?? ''));

if (!$category || !$name || !$email || !$message) {
    echo json_encode(['ok' => false, 'error' => 'All required fields must be filled.']);
    exit;
}

if (strlen($message) < 10) {
    echo json_encode(['ok' => false, 'error' => 'Message too short.']);
    exit;
}

// Honeypot: reject if hidden field is filled (bot detection)
if (!empty($_POST['website_url'])) {
    echo json_encode(['ok' => true]); // Pretend success to bots
    exit;
}

$to = 'gwu0738@gmail.com';
$subject = "[22div.com.au] {$category} enquiry from {$name}";

$body  = "Category: {$category}\n";
$body .= "Name: {$name}\n";
$body .= "Email: {$email}\n";
$body .= "Phone: {$phone}\n\n";
$body .= "Message:\n{$message}\n\n";
$body .= "---\nSent from 22div.com.au contact form\n";
$body .= "IP: {$ip}\n";
$body .= "Time: " . date('Y-m-d H:i:s T') . "\n";

$headers  = "From: admin@22div.com.au\r\n";
$headers .= "Reply-To: {$email}\r\n";
$headers .= "X-Mailer: 22div-contact/1.0\r\n";

$sent = mail($to, $subject, $body, $headers);

if ($sent) {
    touch($lockfile); // Rate limit lock
    echo json_encode(['ok' => true]);
} else {
    echo json_encode(['ok' => false, 'error' => 'Mail server error. Email admin@22div.com.au directly.']);
}
