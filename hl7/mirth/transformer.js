// Mirth Connect JavaScript Transformer for the LCIIS "HL7 ORU Ingestion"
// channel. Paste into the channel's Transformer step (Source connector:
// TCP Listener, MLLP framing; Destination: HTTP Sender).
//
// Converts an inbound ORU^R01 message's PID/PV1/OBX segments into the JSON
// array LCIIS's POST /api/lab-result endpoint expects — see
// backend/app/schemas.py:LabResultIn for the target shape, and
// hl7/hl7_parser.py for the equivalent logic used when running the
// standalone MLLP bridge instead of Mirth.

var patientId = msg['PID']['PID.3']['PID.3.1'].toString();
var lastName = msg['PID']['PID.5']['PID.5.1'].toString();
var firstName = msg['PID']['PID.5']['PID.5.2'].toString();
var patientName = (firstName + ' ' + lastName).trim() || patientId;

var ward = msg['PV1']['PV1.3']['PV1.3.1'].toString();
var bed = msg['PV1']['PV1.3']['PV1.3.2'].toString();

var doctorFamily = msg['PV1']['PV1.7']['PV1.7.2'].toString();
var doctorGiven = msg['PV1']['PV1.7']['PV1.7.3'].toString();
var physician = doctorFamily ? ('Dr. ' + doctorFamily + ' ' + doctorGiven).trim() : null;

var results = [];
var obxCount = msg['OBX'].length();
for (var i = 0; i < obxCount; i++) {
    var obx = msg['OBX'][i];
    var code = obx['OBX.3']['OBX.3.1'].toString();
    var name = obx['OBX.3']['OBX.3.2'].toString() || code;
    var value = parseFloat(obx['OBX.5']['OBX.5.1'].toString());
    if (isNaN(value)) { continue; } // skip free-text / non-numeric OBX rows

    var unit = obx['OBX.6']['OBX.6.1'].toString() || null;
    var refRange = obx['OBX.7'].toString();
    var refLow = null, refHigh = null;
    if (refRange.indexOf('-') > -1) {
        var parts = refRange.split('-');
        refLow = parseFloat(parts[0]);
        refHigh = parseFloat(parts[1]);
    }

    var observedAt = obx['OBX.14']['OBX.14.1'].toString() ||
                      msg['OBR']['OBR.7']['OBR.7.1'].toString();

    results.push({
        patient_id: patientId,
        patient_name: patientName,
        bed: bed || null,
        ward: ward || null,
        test_code: code,
        test_name: name,
        value: value,
        unit: unit,
        ref_low: isNaN(refLow) ? null : refLow,
        ref_high: isNaN(refHigh) ? null : refHigh,
        ordering_physician: physician,
        collected_at: formatHl7Timestamp(observedAt)
    });
}

// One HTTP Sender destination fires per OBX row (Destination Set to
// "Message" iteration in Mirth, or loop with a JavaScript Writer step).
channelMap.put('labResultPayloads', JSON.stringify(results));

function formatHl7Timestamp(ts) {
    // YYYYMMDDHHMMSS -> ISO 8601
    if (!ts || ts.length < 8) { return new Date().toISOString(); }
    var y = ts.substring(0, 4), mo = ts.substring(4, 6), d = ts.substring(6, 8);
    var h = ts.length >= 10 ? ts.substring(8, 10) : '00';
    var mi = ts.length >= 12 ? ts.substring(10, 12) : '00';
    var s = ts.length >= 14 ? ts.substring(12, 14) : '00';
    return y + '-' + mo + '-' + d + 'T' + h + ':' + mi + ':' + s;
}
