import numpy as np
import cv2 as cv

def select_img_from_video(video_file, board_pattern, select_all=False, wait_msec=10, wnd_name='Camera Calibration'):
    video = cv.VideoCapture(video_file)
    assert video.isOpened()

    img_select = []
    while True:
        valid, img = video.read()
        if not valid:
            break

        if select_all:
            img_select.append(img)
        else:
            display = img.copy()
            cv.putText(display, f'NSelect: {len(img_select)}', (10, 25), cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 0))
            cv.imshow(wnd_name, display)

            key = cv.waitKey(wait_msec)
            if key == ord(' '):  # Spacebar: pause and try to detect chessboard
                complete, pts = cv.findChessboardCorners(img, board_pattern)
                if complete:
                    cv.drawChessboardCorners(display, board_pattern, pts, complete)
                else:
                    cv.putText(display, "Chessboard not detected!", (10, 60), cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 255))
                cv.imshow(wnd_name, display)
                key = cv.waitKey()
                if key == 13 or key == 10:  # Enter key (Mac & Windows)
                    img_select.append(img)
            if key == 27:  # ESC: exit
                break

    cv.destroyAllWindows()
    return img_select

def calib_camera_from_chessboard(images, board_pattern, board_cellsize, K=None, dist_coeff=None, calib_flags=None):
    img_points = []
    for img in images:
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        complete, pts = cv.findChessboardCorners(gray, board_pattern)
        if complete:
            img_points.append(pts)
    assert len(img_points) > 0

    obj_pts = [[c, r, 0] for r in range(board_pattern[1]) for c in range(board_pattern[0])]
    obj_points = [np.array(obj_pts, dtype=np.float32) * board_cellsize] * len(img_points)
 
    return cv.calibrateCamera(obj_points, img_points, gray.shape[::-1], K, dist_coeff, flags=calib_flags)

if __name__ == '__main__':
    video_file = 'Video.MOV'
    board_pattern = (8,6)
    board_cellsize = 0.025

    # Step 1: 영상에서 체스보드 이미지 선택
    img_select = select_img_from_video(video_file, board_pattern)
    assert len(img_select) > 0, 'There is no selected images!'

    # Step 2: 카메라 보정
    rms, K, dist_coeff, rvecs, tvecs = calib_camera_from_chessboard(img_select, board_pattern, board_cellsize)

    print('## Camera Calibration Results')
    print(f'* The number of selected images = {len(img_select)}')
    print(f'* RMS error = {rms}')
    print(f'* Camera matrix (K) = \n{K}')
    print(f'* Distortion coefficient (k1, k2, p1, p2, k3, ...) = {dist_coeff.flatten()}')

    # Step 3: 왜곡 보정 전/후 영상 비교
    video = cv.VideoCapture(video_file)
    assert video.isOpened(), 'Cannot read the given input, ' + video_file

    show_rectify = True
    map1, map2 = None, None
    while True:
        valid, img = video.read()
        if not valid:
            break

        display = img.copy()
        info = "Original"

        if show_rectify:
            if map1 is None or map2 is None:
                map1, map2 = cv.initUndistortRectifyMap(K, dist_coeff, None, K, (img.shape[1], img.shape[0]), cv.CV_32FC1)
            display = cv.remap(img, map1, map2, interpolation=cv.INTER_LINEAR)
            info = "Rectified"

        cv.putText(display, info, (10, 25), cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 0))
        cv.imshow("Geometric Distortion Correction", display)

        key = cv.waitKey(10)
        if key == ord(' '):  # 일시 정지
            key = cv.waitKey()
        if key == 27:  # ESC
            break
        elif key == ord('\t'):  # Tab: 원본/보정 토글
            show_rectify = not show_rectify

    video.release()
    cv.destroyAllWindows()
