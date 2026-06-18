autocannon -c 10 -p 1 -d 20 -m POST -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ZTA0NTljNC05OTEzLTQzNzMtOWI4YS1kYTcxOTQ0MWU1YmMiLCJqdGkiOiIzMDUwOTVkMi1jN2Q0LTRlMDYtODBjYy0zN2VkNzg3ODJlNDQiLCJ0eXBlIjoiYWNjZXNzIiwiZnJlc2giOmZhbHNlLCJjc3JmIjoiYjY5ZTg2NTgtZGYwNS00MDFhLWI5YzItYzdlNGVmNGNhNzY1IiwiaWF0IjoxNzgxNTUxNDU4LCJleHAiOjE3ODE1NTIzNTguMzMyNDV9.Ankn3BI48rufRm-pss4STq201fXOC4QRIDdlrP4WZvg" http://localhost:5000/mock/refresh
autocannon -c 50 -p 1 -d 20 -m POST -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ZTA0NTljNC05OTEzLTQzNzMtOWI4YS1kYTcxOTQ0MWU1YmMiLCJqdGkiOiIzMDUwOTVkMi1jN2Q0LTRlMDYtODBjYy0zN2VkNzg3ODJlNDQiLCJ0eXBlIjoiYWNjZXNzIiwiZnJlc2giOmZhbHNlLCJjc3JmIjoiYjY5ZTg2NTgtZGYwNS00MDFhLWI5YzItYzdlNGVmNGNhNzY1IiwiaWF0IjoxNzgxNTUxNDU4LCJleHAiOjE3ODE1NTIzNTguMzMyNDV9.Ankn3BI48rufRm-pss4STq201fXOC4QRIDdlrP4WZvg" http://localhost:5000/mock/refresh
autocannon -c 100 -p 2 -d 20 -m POST -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ZTA0NTljNC05OTEzLTQzNzMtOWI4YS1kYTcxOTQ0MWU1YmMiLCJqdGkiOiJjY2RkM2U5Mi03YjAxLTRjOTgtODVkNC0zN2FmZjM5ODkxYTgiLCJ0eXBlIjoiYWNjZXNzIiwiZnJlc2giOmZhbHNlLCJjc3JmIjoiYWQ0NjcyZmUtOGViZS00YzRkLWFkZTgtZjViYjFkNjUwOTY3IiwiaWF0IjoxNzgxNTUyNDUwLCJleHAiOjE3ODE1NTMzNTAuMzg1NTk2fQ.1w4-iiU-wKIsg3wDvPET21ebHronrEDH1Mb7WoeXPTw" http://localhost:5000/mock/refresh
autocannon -c 250 -p 2 -d 20 -m POST -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ZTA0NTljNC05OTEzLTQzNzMtOWI4YS1kYTcxOTQ0MWU1YmMiLCJqdGkiOiJjY2RkM2U5Mi03YjAxLTRjOTgtODVkNC0zN2FmZjM5ODkxYTgiLCJ0eXBlIjoiYWNjZXNzIiwiZnJlc2giOmZhbHNlLCJjc3JmIjoiYWQ0NjcyZmUtOGViZS00YzRkLWFkZTgtZjViYjFkNjUwOTY3IiwiaWF0IjoxNzgxNTUyNDUwLCJleHAiOjE3ODE1NTMzNTAuMzg1NTk2fQ.1w4-iiU-wKIsg3wDvPET21ebHronrEDH1Mb7WoeXPTw" http://localhost:5000/mock/refresh

autocannon -c 10 -p 1 -d 20 --timeout 15 http://localhost:5000/mock/offers/999
autocannon -c 50 -p 1 -d 20 --timeout 15 http://localhost:5000/mock/offers/999
autocannon -c 100 -p 2 -d 20 --timeout 15 http://localhost:5000/mock/offers/999
autocannon -c 250 -p 2 -d 20 --timeout 15 http://localhost:5000/mock/offers/999

autocannon -c 10 -p 1 -d 60 --timeout 15 http://localhost:5000/mock/discovery/stream/999
autocannon -c 50 -p 1 -d 60 --timeout 15 http://localhost:5000/mock/discovery/stream/999
autocannon -c 100 -p 1 -d 60 --timeout 15 http://localhost:5000/mock/discovery/stream/999
autocannon -c 250 -p 1 -d 60 --timeout 15 http://localhost:5000/mock/discovery/stream/999

autocannon -c 20 -p 1 -d 30 --timeout 120 -m POST \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ZTA0NTljNC05OTEzLTQzNzMtOWI4YS1kYTcxOTQ0MWU1YmMiLCJqdGkiOiIyZTBlYjIwZS1iOWQwLTQxMTYtYWUyZC0wMzdlZjdhMjk4MjUiLCJ0eXBlIjoiYWNjZXNzIiwiZnJlc2giOmZhbHNlLCJjc3JmIjoiYWUwMjUxMjAtZmE4Yy00YWE1LTkxZDgtMDIzMzFiY2YyN2FlIiwiaWF0IjoxNzgxNzAyMjE2LCJleHAiOjE3ODE3MDMxMTYuODQ4Mzk0fQ.fHg6gYMcYr4Gw7PnHSzo2k6EeJ-qdT7JiM4RLkyD4Qo" \
  -H "Content-Type: application/json" \
  -b '{"session_id": 1, "action": "generate_schedule"}' \
  http://localhost:5000/itinerary/schedule/action

autocannon -c 20 -p 1 -d 60 --timeout 30 -m POST \
  -H "Authorization: Bearer INCOPIE_AICI_TOKEN_NOU_DIN_BROWSER" \
  -H "Content-Type: application/json" \
  -b '{"session_id": 1, "action": "generate_schedule"}' \
  http://localhost:5000/itinerary/schedule/action

autocannon -c 50 -p 1 -d 60 --timeout 30 -m POST \
  -H "Authorization: Bearer INCOPIE_AICI_TOKEN_NOU_DIN_BROWSER" \
  -H "Content-Type: application/json" \
  -b '{"session_id": 1, "action": "generate_schedule"}' \
  http://localhost:5000/itinerary/schedule/action