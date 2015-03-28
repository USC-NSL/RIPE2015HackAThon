<!DOCTYPE html>
<html>
<h1>HackMyDNS</h1>

<?php




$servername = "localhost";
$username = "";
$password = "";
$dbname = "measurement";
// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
} 
//echo "Connected successfully";

$measurement_type=$_GET["m_type"];
$dest_list=$_GET["dest_list"];
$interval=$_GET["interval"];
$uuid=gen_uuid();
$uuid=$uuid.'.m.ripeatlasdns.net';

$sql = "INSERT INTO measurement (measurement_type, destination_list, measurement_interval,hostname)
VALUES ('$measurement_type', '$dest_list', '$interval','$uuid')";

if ($conn->query($sql) === TRUE) {
echo 'Hostname: '.$uuid;
//    echo "New record created successfully";
} else {
    echo "Error: " . $sql . "<br>" . $conn->error;
}

function gen_uuid() {
    return sprintf( '%04x%04x%04x%04x%04x%04x%04x%04x',
//    return sprintf( '%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
        // 32 bits for "time_low"
        mt_rand( 0, 0xffff ), mt_rand( 0, 0xffff ),

        // 16 bits for "time_mid"
        mt_rand( 0, 0xffff ),

        // 16 bits for "time_hi_and_version",
        // asdfour most significant bits holds version number 4
        mt_rand( 0, 0x0fff ) | 0x4000,

        // 16 bits, 8 bits for "clk_seq_hi_res",
        // 8 bits for "clk_seq_low",
        // two most significant bits holds zero and one for variant DCE1.1
        mt_rand( 0, 0x3fff ) | 0x8000,

        // 48 bits for "node"
        mt_rand( 0, 0xffff ), mt_rand( 0, 0xffff ), mt_rand( 0, 0xffff )
    );
}


?>
</html>
