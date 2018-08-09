"""
Example showing how to communicate with an SHOT-702 from OptoSigma.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import time

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

    record = EquipmentRecord(
        manufacturer='OptoSigma',
        model='SHOT-702',
        connection=ConnectionRecord(
            address='COM5',  # update for your serial port number
            backend=Backend.MSL,
            properties=dict(
                termination='\r\n',
                timeout=2,
                baud_rate=38400,
            ),
        )
    )

    def show_status(*args):
        print('  position1={}, position2={}, stopped={}, is_moving={}'.format(*args))

    shot = record.connect()

    # move stage 1 to the home position
    print('Homing...')
    shot.home(1)

    # wait for the stage to finish moving while printing the status to stdout
    shot.wait(show_status)

    # move stage 1 to a position
    print('Move to 100000...')
    shot.move_absolute(1, 100000)

    # wait for the stage to finish moving while printing the status to stdout
    shot.wait(show_status)

    # move stage 1 by -10000
    print('Move by -10000...')
    shot.move_relative(1, -10000)

    # wait for the stage to finish moving while printing the status to stdout
    shot.wait(show_status)

    # get the status of the stages
    status = shot.status()
    print('position1={}, position2={}, stopped={}, is_moving={}'.format(*status))

    # start moving stage 1 at the minimum speed in the + direction for 5 seconds
    print('Start moving stage 1...')
    shot.move(1, '+')
    time.sleep(5)

    # slowly stop stage 1
    print('Stopping stage 1')
    shot.stop_slowly(1)

    # get the status of the stages
    status = shot.status()
    print('position1={}, position2={}, stopped={}, is_moving={}'.format(*status))

    # disconnect from the controller
    shot.disconnect()
