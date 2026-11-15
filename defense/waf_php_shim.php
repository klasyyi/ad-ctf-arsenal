<?php
/**
 * ==============================================================================
 * ZERO-FIREWALL PHP WAF & LOGGING SHIM
 * ==============================================================================
 * Hook this into any PHP challenge:
 * Option A: In php.ini or .user.ini:
 *   auto_prepend_file = /path/to/waf_php_shim.php
 * Option B: At line 1 of index.php:
 *   require_once __DIR__ . '/waf_php_shim.php';
 * ==============================================================================
 */

$log_file = '/tmp/php_waf_traffic.log';

// 1. Capture request context
$request_data = [
    'time'       => date('Y-m-d H:i:s'),
    'remote_ip'  => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
    'uri'        => $_SERVER['REQUEST_URI'] ?? '',
    'method'     => $_SERVER['REQUEST_METHOD'] ?? '',
    'get'        => $_GET,
    'post'       => $_POST,
    'headers'    => getallheaders(),
    'raw_body'   => file_get_contents('php://input')
];

file_put_contents($log_file, json_encode($request_data) . "\n", FILE_APPEND | LOCK_EX);

// 2. Exploit signatures (SQLi, LFI, RCE, Flag exfiltration)
$bad_signatures = [
    '/union\s+select/i',
    '/\/\.\.\//',                                      // Path traversal
    '/(system|exec|passthru|shell_exec|popen)\s*\(/i', // Dangerous sinks
    '/(cat|head|tail|more|less|tac)\s+.*flag/i',        // Shell flag reading
    '/flag\{/i'
];

$raw_str = serialize($_GET) . serialize($_POST) . $request_data['raw_body'];

foreach ($bad_signatures as $pattern) {
    if (preg_match($pattern, $raw_str)) {
        file_put_contents('/tmp/php_blocked_attacks.log', 
            sprintf("[%s] Blocked signature %s from %s\n", 
                date('Y-m-d H:i:s'), 
                $pattern,
                $request_data['remote_ip']
            ), 
            FILE_APPEND
        );

        // SAFE DEFENSE: Return 200 OK so SLA checker does not fail with 500 error!
        header('HTTP/1.1 200 OK');
        die('Request completed.');
    }
}
?>
