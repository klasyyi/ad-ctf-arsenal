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
 * Mode (env var WAF_MODE):
 *   "monitor" (default) - log matches, NEVER block. A false positive costs only
 *       a log line, never the SLA check.
 *   "block"             - additionally 403 on a match. Use only after watching
 *       the monitor log against real checker traffic. Blocking CAN fail SLA on a
 *       false positive; a fake 200 does not help, the checker needs real content.
 *
 * Deliberately NOT matched: the flag format itself. The organizer SLA checker
 * plants and reads flags through legit endpoints, so matching on the flag string
 * blocks the checker and loses SLA.
 * ==============================================================================
 */

$waf_mode = strtolower(getenv('WAF_MODE') ?: 'monitor'); // "monitor" or "block"
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
];

$raw_str = serialize($_GET) . serialize($_POST) . $request_data['raw_body'];

foreach ($bad_signatures as $pattern) {
    if (preg_match($pattern, $raw_str)) {
        $verb = ($waf_mode === 'block') ? 'BLOCKED' : 'WOULD-BLOCK';
        file_put_contents('/tmp/php_blocked_attacks.log',
            sprintf("[%s] %s signature %s from %s\n",
                date('Y-m-d H:i:s'),
                $verb,
                $pattern,
                $request_data['remote_ip']
            ),
            FILE_APPEND
        );

        // Only drop the request in block mode. In monitor mode log and fall
        // through so legit/checker traffic always gets the real app response.
        // 403 is honest: a fake 200 still fails SLA on a false positive.
        if ($waf_mode === 'block') {
            http_response_code(403);
            die('Forbidden.');
        }
        break;
    }
}
?>
