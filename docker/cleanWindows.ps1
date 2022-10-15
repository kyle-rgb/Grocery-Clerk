# reformat vhdx for previous build images 
wsl --shutdown
diskpart
select vdisk --file="%LOCALAPPDATA%\Docker\wsl\data\ext4.vhdx"
attach vdisk readonly
compact vdisk
detach vdisk
exit