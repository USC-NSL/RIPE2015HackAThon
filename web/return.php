<!DOCTYPE html>
<html>
<h1>RIPE Atlas DNS</h1>

<?php

include("../db_settings.php");

error_reporting(E_ERROR | E_PARSE);

try {

    $conn = new PDO($db_url, $db_user, $db_pass, array(PDO::ATTR_PERSISTENT => true));

    if(!isset($_GET["m_type"]) || !isset($_GET["dest_list"]) || !isset($_GET["interval"])){
        throw new Exception('Missing parameter.');
    }

    $measurement_type = $_GET["m_type"];
    
    $dest_list = $_GET["dest_list"];
    $dest_list = preg_replace('#\s+#',',', trim($dest_list)); //replace any newlines with commas
    list($dest_valid, $dest_issue) = validate($dest_list);
    if(!$dest_valid){
        throw new Exception("Destination list must contain valid IPs or hostnames. '" . $dest_issue . "' is not valid.");
    }

    $interval = $_GET["interval"];
    $uuid = gen_uuid();

    $hostname = $uuid.'.m.ripeatlasdns.net';

    //$sql = "INSERT INTO measurement (measurement_type, destination_list, measurement_interval,hostname) VALUES ('$measurement_type', '$dest_list', '$interval','$uuid')";

    $stmt = $conn->prepare("INSERT INTO measurement (measurement_type, destination_list, measurement_interval, hostname) VALUES (:mtype, :dlist, :minterval, :hostname)");

    $stmt->bindParam(':mtype', $measurement_type, PDO::PARAM_INT);
    $stmt->bindParam(':dlist', $dest_list, PDO::PARAM_STR);
    $stmt->bindParam(':minterval', $interval, PDO::PARAM_INT);
    $stmt->bindParam(':hostname', $hostname, PDO::PARAM_STR, 100);

    $result = $stmt->execute();

    if ($result) {
        echo 'Hostname: '.$hostname;
    } else {
        echo 'Unknown Error <br>';
    }

    $stmt->closeCursor();

} catch (Exception $e) {
    print "Error!: " . $e->getMessage() . "<br/>";
    die();
} finally {
    if($conn){
        $conn = null;
    }
}

function validate($dests)
{
    //split the comma delimited string into an array
    $dest_array = explode(",", $dests);

    foreach ($dest_array as $dest) {
        if(!inet_pton($dest) && !fqdn($dest)){
            //if not a valid IP or fully qualified domain name, return false
            return array(false, $dest);
        }
    }

    return array(true, '');
}

function fqdn($domain_name)
{
    
    $label_array = explode(".", $domain_name);

    $domain_count = count($label_array);
    if($domain_count < 2){
        return false;
    }

    $tld = array_pop($label_array);
    if(strlen($tld) < 2 || !ctype_alpha($tld)){
        return false;
    }

    return preg_match("/^([a-z\d](-*[a-z\d])*)(\.([a-z\d](-*[a-z\d])*))*$/i", $domain_name); //valid chars check
    //        && preg_match("/^.{1,253}$/", $domain_name)   //overall length check
    //        && preg_match("/^[^\.]{1,63}(\.[^\.]{1,63})*$/", $domain_name)   ); //length of each label
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
