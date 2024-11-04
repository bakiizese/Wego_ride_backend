data = [('60d33c0a-8b05-4665-a5e9-6ac2455eab3e','Corolla','NULL','White',3,'301aac56-ca95-4afd-8f81-b5583cea23e2','2024-10-15 14:05:55','2024-10-15 14:05:55'),('8f0302cb-0e0e-4ad6-b2f6-839f71fccde0','nisan','NULL','Black',4,'772cdad2-3065-4474-bf7d-cc244f6a18dc','2024-10-15 14:05:07','2024-10-15 14:05:07'),('85f1c9be-aba8-4b80-8613-4925c1964eb4','Corolla','NULL','White',3,'a3d86838-1032-4176-ab5e-e8f77a38f2a3','2024-10-15 14:05:42','2024-10-15 14:05:42'),('dad730e7-d777-4e95-9774-1d205dc533c0','Vitz','NULL','Red',3,'d57c3f29-521f-4f6e-96f7-353fede215d4','2024-10-15 14:04:11','2024-10-15 14:04:11')]
new_data = []
for d in data:
    new_tuple = (d[5], d[6], d[7], d[0], d[1], d[2], d[3], d[4])
    new_data.append(new_tuple)
print(new_data)